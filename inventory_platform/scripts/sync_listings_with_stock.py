"""sync_listings_with_stock.py — Sincroniza publicaciones MELI contra stock real.

Por cada listing activo en el sistema:
  - Si su SKU tiene stock=0 en el warehouse correspondiente: PAUSA el listing en MELI.
  - Si tiene stock>0 y el available_quantity del listing en MELI difiere: UPDATE available_quantity.
  - Si está paused y el SKU vuelve a tener stock: REACTIVA (opcional --auto-reactivate).

Multi-account aware: para cada listing, usa el token de la cuenta dueña.
MELI Full: para Full, MELI gestiona inventario directo — sólo pausamos si stock=0.

Idempotente. Reporta cambios. Mandar a Telegram si hay >0 acciones.

Uso:
    SUPABASE_DB_URL=... TOKEN_READ_SECRET=... WORKER_BASE=... \\
        python sync_listings_with_stock.py [--dry-run] [--auto-reactivate]
        [--account NICK] [--max-seconds 280]
"""
import os, sys, time, argparse, requests, psycopg2
from concurrent.futures import ThreadPoolExecutor

DSN = os.environ["SUPABASE_DB_URL"]
WORKER_BASE = os.environ.get("WORKER_BASE","https://meli-webhook.elite-market-1779161651.workers.dev").rstrip("/")
TOKEN_READ_SECRET = os.environ.get("TOKEN_READ_SECRET","")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT  = os.environ.get("TELEGRAM_CHAT_ID")


def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass


def get_token(nick):
    try:
        r = requests.get(f"{WORKER_BASE}/token/{nick}",
                         headers={"Authorization": f"Bearer {TOKEN_READ_SECRET}"}, timeout=20)
        return r.json().get("access_token") if r.status_code == 200 else None
    except Exception:
        return None


def get_item(mlm, tok):
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{mlm}",
                         params={"attributes":"id,available_quantity,status,sub_status,shipping,catalog_listing"},
                         headers={"Authorization": f"Bearer {tok}"}, timeout=20)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def update_item(mlm, tok, body):
    """PUT /items/{mlm}. body = dict con campos a actualizar."""
    try:
        r = requests.put(f"https://api.mercadolibre.com/items/{mlm}",
                         headers={"Authorization": f"Bearer {tok}", "Content-Type":"application/json"},
                         json=body, timeout=30)
        return r.status_code, (r.json() if r.status_code < 500 else r.text[:200])
    except Exception as e:
        return 0, str(e)[:200]


def is_full(item):
    """Detecta si un listing está en MELI Full (fulfillment) — no debemos cambiar available_quantity."""
    if not item: return False
    ship = item.get("shipping") or {}
    return ship.get("logistic_type") in ("fulfillment","cross_docking_drop_off") \
        or item.get("catalog_listing") is True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--auto-reactivate", action="store_true",
                    help="reactivar paused cuando hay stock (default: solo log, no reactiva)")
    ap.add_argument("--account", default=None)
    ap.add_argument("--max-seconds", type=int, default=280)
    ap.add_argument("--only-seeded", action="store_true",
                    help="solo pausar SKUs que tuvieron seed inicial (más seguro)")
    args = ap.parse_args()
    t0 = time.time()

    conn = psycopg2.connect(DSN); conn.autocommit = True; cur = conn.cursor()

    # Mapa de stock por (sku, warehouse)
    cur.execute("SELECT sku, warehouse, qty FROM stock")
    stock_map = {(r[0], r[1]): r[2] for r in cur.fetchall()}

    # SKUs que han sido seedeados (tuvieron initial_seed) — para safety
    cur.execute("SELECT DISTINCT sku FROM stock_movements WHERE movement_type='initial_seed'")
    seeded_skus = set(r[0] for r in cur.fetchall())
    print(f"🛡  SKUs con seed inicial: {len(seeded_skus)} (--only-seeded={args.only_seeded})")

    # Listings con su account y nick
    where = ""
    params = []
    if args.account:
        where = "WHERE upper(a.nickname) = upper(%s)"
        params = [args.account]
    cur.execute(f"""
        SELECT l.mlm_id, l.account_id, a.nickname, l.sku, l.warehouse_default, l.status, l.title
          FROM listings l JOIN accounts a ON a.id=l.account_id
         {where}
         AND a.active=true
    """.replace("AND" if args.account else "WHERE","WHERE" if not args.account else "AND"), params or None)
    rows = cur.fetchall()
    print(f"📋 listings a inspeccionar: {len(rows)}")

    # Tokens por nick (cargar concurrentes)
    nicks_needed = list(set((r[2] or "").upper() for r in rows))
    toks = {}
    def gtok(n):
        return n, get_token(n)
    with ThreadPoolExecutor(max_workers=8) as ex:
        for n, t in ex.map(gtok, nicks_needed):
            if t: toks[n] = t
    print(f"🔑 tokens cargados: {len(toks)}/{len(nicks_needed)}")

    actions = {"paused":0, "reactivated":0, "qty_updated":0, "kept":0, "skipped_full":0, "no_token":0, "errors":[]}
    samples_paused = []; samples_qty = []

    def fetch_item(row):
        mlm, aid, nick, sku, wh, status, title = row
        nick = (nick or "").upper()
        tk = toks.get(nick)
        if not tk:
            return (row, None, None)
        item = get_item(mlm, tk)
        return (row, item, tk)

    with ThreadPoolExecutor(max_workers=20) as ex:
        for row, item, tk in ex.map(fetch_item, rows):
            if time.time() - t0 > args.max_seconds:
                print("⏱ max-seconds alcanzado, corto"); break
            mlm, aid, nick, sku, wh, db_status, title = row
            nick_u = (nick or "").upper()
            if not tk:
                actions["no_token"] += 1
                continue
            if not item:
                continue
            stock_qty = stock_map.get((sku, wh), 0)
            real_status = item.get("status")
            real_qty = int(item.get("available_quantity") or 0)
            full = is_full(item)

            # CASO 1: stock = 0
            if stock_qty <= 0:
                # SAFETY: si --only-seeded, no pausar SKUs sin seed inicial
                if args.only_seeded and sku not in seeded_skus:
                    actions["kept"] += 1
                    continue
                if real_status == "paused":
                    actions["kept"] += 1
                    continue
                # pause
                if args.dry_run:
                    print(f"  [DRY] PAUSE {mlm} sku={sku} stock=0 status_actual={real_status}")
                else:
                    code, body = update_item(mlm, tk, {"status":"paused"})
                    if 200 <= code < 300:
                        actions["paused"] += 1
                        cur.execute("UPDATE listings SET status='paused', last_sync=now() WHERE mlm_id=%s", (mlm,))
                        if len(samples_paused) < 15: samples_paused.append(f"{nick_u}/{mlm} {sku}")
                    else:
                        actions["errors"].append(f"pause {mlm}: HTTP {code} {str(body)[:80]}")
                continue

            # CASO 2: stock > 0, listing paused → reactivar (si --auto-reactivate)
            if real_status == "paused" and stock_qty > 0:
                if args.auto_reactivate and not full:
                    if args.dry_run:
                        print(f"  [DRY] REACTIVATE {mlm} sku={sku} stock={stock_qty}")
                    else:
                        code, body = update_item(mlm, tk, {"status":"active","available_quantity": stock_qty})
                        if 200 <= code < 300:
                            actions["reactivated"] += 1
                            cur.execute("UPDATE listings SET status='active', last_sync=now() WHERE mlm_id=%s", (mlm,))
                        else:
                            actions["errors"].append(f"reactivate {mlm}: HTTP {code} {str(body)[:80]}")
                else:
                    actions["kept"] += 1
                continue

            # CASO 3: active y stock > 0 → sync available_quantity
            if real_status == "active":
                if full:
                    # MELI Full gestiona qty; no tocar
                    actions["skipped_full"] += 1
                    continue
                if real_qty != stock_qty and stock_qty > 0:
                    if args.dry_run:
                        print(f"  [DRY] SET qty {mlm} sku={sku} {real_qty}→{stock_qty}")
                    else:
                        code, body = update_item(mlm, tk, {"available_quantity": stock_qty})
                        if 200 <= code < 300:
                            actions["qty_updated"] += 1
                            if len(samples_qty) < 10: samples_qty.append(f"{nick_u}/{mlm} {sku} {real_qty}→{stock_qty}")
                        else:
                            actions["errors"].append(f"qty {mlm}: HTTP {code} {str(body)[:80]}")
                else:
                    actions["kept"] += 1

    print(f"\n=== Resumen sync_listings ===")
    print(f"  ⏸ pausados        : {actions['paused']}")
    print(f"  ▶ reactivados     : {actions['reactivated']}")
    print(f"  🔢 qty actualizados: {actions['qty_updated']}")
    print(f"  ✓ sin cambios     : {actions['kept']}")
    print(f"  ⛵ Full (skip qty) : {actions['skipped_full']}")
    print(f"  🔒 sin token      : {actions['no_token']}")
    if actions["errors"]:
        print(f"  ❌ errores ({len(actions['errors'])}):")
        for e in actions["errors"][:8]: print(f"     {e}")

    if samples_paused:
        print("\n  ⏸ Ejemplos pausados:")
        for s in samples_paused: print(f"     {s}")
    if samples_qty:
        print("\n  🔢 Ejemplos qty actualizados:")
        for s in samples_qty: print(f"     {s}")

    # Telegram alert si hay cambios
    if not args.dry_run and (actions['paused'] or actions['reactivated'] or actions['qty_updated'] or actions['errors']):
        msg = "🔄 *Sync listings ↔ stock*\n"
        if actions['paused']: msg += f"⏸ Pausados (stock=0): *{actions['paused']}*\n"
        if actions['reactivated']: msg += f"▶ Reactivados: *{actions['reactivated']}*\n"
        if actions['qty_updated']: msg += f"🔢 Cantidad ajustada: *{actions['qty_updated']}*\n"
        if actions['errors']: msg += f"❌ Errores: {len(actions['errors'])}\n"
        if samples_paused:
            msg += "\nPausados:\n" + "\n".join(f"• `{s}`" for s in samples_paused[:8])
        tg(msg)

    cur.close(); conn.close()


if __name__ == "__main__":
    main()
