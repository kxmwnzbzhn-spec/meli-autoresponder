"""Snapshot point-in-time de órdenes paid+no-enviadas por cuenta MELI.

Para reconciliación go-live: se corre JUSTO ANTES de contar stock físico.
Captura todas las órdenes que ya cobramos pero no hemos despachado, para
que después go_live_seed.py decremente del conteo físico y deje el stock real.

Uso:
    SUPABASE_DB_URL=... MELI_APP_ID=... MELI_APP_SECRET=... \\
        MELI_REFRESH_TOKEN_WILBERT=... ... \\
        python snapshot_pending_orders.py [--days-back 30]

Output:
    - Inserta filas en pending_orders_snapshot (mismo snapshot_batch UUID por run)
    - Alerta Telegram con resumen por cuenta + por SKU
"""
import os, sys, json, argparse, requests, psycopg2, uuid
from datetime import datetime, timedelta, timezone

parser = argparse.ArgumentParser()
parser.add_argument("--days-back", type=int, default=30,
                    help="Solo órdenes pagadas en los últimos N días (default 30)")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

DSN = os.environ["SUPABASE_DB_URL"]
CID = os.environ["MELI_APP_ID"]
CS = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

NOT_SHIPPED_STATUSES = {"pending", "handling", "ready_to_ship", "to_be_agreed", None}
# Si shipping.status es uno de estos → la orden NO ha salido del almacén


def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        print(f"[no telegram] {msg}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        print(f"telegram failed: {e}")


def refresh_token(rt):
    r = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={"grant_type": "refresh_token",
              "client_id": CID, "client_secret": CS,
              "refresh_token": rt},
        timeout=20,
    )
    if r.status_code != 200:
        return None, r.text
    return r.json().get("access_token"), None


def fetch_orders(user_id, access_token, days_back):
    """Pagina /orders/search?seller=user_id&order.status=paid"""
    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    H = {"Authorization": f"Bearer {access_token}"}
    orders = []
    offset = 0
    limit = 50
    while True:
        params = {
            "seller": user_id,
            "order.status": "paid",
            "sort": "date_desc",
            "limit": limit,
            "offset": offset,
            "order.date_created.from": since,
        }
        r = requests.get("https://api.mercadolibre.com/orders/search",
                         headers=H, params=params, timeout=30)
        if r.status_code != 200:
            print(f"  ✗ orders/search status={r.status_code}: {r.text[:200]}")
            break
        body = r.json()
        results = body.get("results", [])
        orders.extend(results)
        total = body.get("paging", {}).get("total", 0)
        if offset + limit >= total or not results:
            break
        offset += limit
        if offset > 5000:
            print(f"  ⚠ stopping at offset {offset}, demasiadas órdenes")
            break
    return orders


def fetch_shipping(shipping_id, access_token):
    if not shipping_id:
        return None
    H = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"https://api.mercadolibre.com/shipments/{shipping_id}",
                     headers=H, timeout=20)
    if r.status_code != 200:
        return None
    return r.json()


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT id, nickname, meli_user_id, refresh_token_secret FROM accounts WHERE active = true ORDER BY nickname")
    accounts = cur.fetchall()
    if not accounts:
        msg = "⚠️ No hay accounts activos. Corre inv_backfill_accounts primero."
        print(msg); tg(msg); sys.exit(1)

    batch_uuid = str(uuid.uuid4())
    print(f"📦 Snapshot batch: {batch_uuid}")
    print(f"📅 Lookback: {args.days_back} días")

    cur.execute("SELECT mlm_id, sku FROM listings")
    mlm_to_sku = dict(cur.fetchall())
    print(f"🗂  Listings mapeo: {len(mlm_to_sku)} MLM→SKU")

    grand_total_pending = 0
    grand_total_orders = 0
    per_account = {}

    for aid, nick, user_id, secret_name in accounts:
        print(f"\n--- {nick} (user_id={user_id}) ---")
        rt = os.environ.get(secret_name, "").strip()
        if not rt:
            print(f"  ⚠ no secret {secret_name}, skip")
            continue
        access_token, err = refresh_token(rt)
        if not access_token:
            print(f"  ✗ refresh failed: {err[:200] if err else 'unknown'}")
            continue

        orders = fetch_orders(user_id, access_token, args.days_back)
        print(f"  fetched {len(orders)} paid orders en últimos {args.days_back}d")

        account_pending = 0
        for order in orders:
            order_id = str(order.get("id"))
            shipping = order.get("shipping") or {}
            shipping_id = shipping.get("id")
            ship_detail = fetch_shipping(shipping_id, access_token) if shipping_id else None
            ship_status = (ship_detail or {}).get("status")

            # Si tiene shipping y ya salió → skip
            if ship_status not in NOT_SHIPPED_STATUSES:
                continue

            # Esta orden está PENDIENTE
            for it in (order.get("order_items") or []):
                item = it.get("item", {})
                mlm = item.get("id")
                qty = int(it.get("quantity", 0) or 0)
                if qty <= 0:
                    continue
                sku = mlm_to_sku.get(mlm)
                unit_price = it.get("unit_price")
                total_amount = (unit_price or 0) * qty
                date_paid = order.get("date_closed") or order.get("last_updated")
                date_created = order.get("date_created")
                buyer = (order.get("buyer") or {}).get("nickname")

                if args.dry_run:
                    print(f"    [DRY] {order_id} {mlm} sku={sku} qty={qty}")
                    continue

                cur.execute(
                    """
                    INSERT INTO pending_orders_snapshot
                        (snapshot_batch, order_id, account_id, mlm_id, sku, qty,
                         unit_price, total_amount, date_paid, date_created,
                         shipping_status, shipping_id, buyer_nick, raw_order, raw_shipping)
                    VALUES (%s,%s,%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s,%s)
                    """,
                    (
                        batch_uuid, order_id, aid, mlm, sku, qty,
                        unit_price, total_amount, date_paid, date_created,
                        ship_status, str(shipping_id) if shipping_id else None, buyer,
                        json.dumps(order), json.dumps(ship_detail) if ship_detail else None,
                    ),
                )
                account_pending += qty

        per_account[nick] = account_pending
        grand_total_pending += account_pending
        grand_total_orders += len(orders)
        print(f"  → {account_pending} units pendientes")

    if not args.dry_run:
        conn.commit()

    # Resumen por SKU
    cur.execute("SELECT sku, SUM(qty), COUNT(*) FROM pending_orders_snapshot WHERE snapshot_batch=%s GROUP BY sku ORDER BY SUM(qty) DESC", (batch_uuid,))
    by_sku = cur.fetchall()

    summary = [
        f"📸 *Pending orders snapshot*",
        f"Batch: `{batch_uuid}`",
        f"Total pendientes: *{grand_total_pending}* units",
        "",
        "*Por cuenta:*",
    ]
    for nick, n in sorted(per_account.items(), key=lambda x: -x[1]):
        if n > 0:
            summary.append(f"  • `{nick}`: {n}")

    summary.append("")
    summary.append(f"*Top 10 SKUs ({len(by_sku)} totales):*")
    for sku, qty, n_orders in by_sku[:10]:
        sku_str = sku or "_(no mapeado)_"
        summary.append(f"  • `{sku_str}`: {qty} units / {n_orders} órdenes")

    msg = "\n".join(summary)
    print("\n" + msg)
    tg(msg)

    cur.close()
    conn.close()
    print(f"\n✓ Snapshot completado. batch={batch_uuid}")
    return batch_uuid


if __name__ == "__main__":
    main()
