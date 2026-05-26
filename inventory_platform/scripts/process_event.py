"""process_event.py — Consumidor de eventos MELI → stock + COGS.

El Worker Cloudflare recibe webhooks y los persiste en `events` (processing_status='pending').
Este script consume esos eventos pendientes y aplica el efecto en inventario:

  orders_v2 / orders  → por cada item de la orden PAGADA:
      resolve_sale_target(mlm_id, variation_id) → (sku, warehouse)
      apply_stock_delta(-qty, type='sale', order_id, ...) → movement_id
      consume_cost(sku, warehouse, qty, order_id, movement_id) → COGS

  post_purchase / claims → process_return(...) (devolución vuelve a inventario 'devolucion')

Garantías:
  • IDEMPOTENTE por order_id: si la orden ya tiene un movimiento 'sale' en
    stock_movements, NO se vuelve a descontar (protege contra el go-live seed
    y contra los multiples webhooks que MELI manda por la misma orden).
  • Solo descuenta órdenes con status 'paid' (o 'partially_paid'). Webhooks de
    órdenes no pagadas se marcan procesados sin tocar stock; cuando llegue el
    webhook de pago, esa orden se procesa (aún no tiene movimiento 'sale').
  • TOKENS: nunca llama /oauth/token. Lee el access_token vigente del Worker
    (autoridad central) vía GET {WORKER_BASE}/token/{ACCOUNT}.
  • --since permite un watermark de go-live para no procesar órdenes anteriores
    al conteo físico.

Uso:
    SUPABASE_DB_URL=... TOKEN_READ_SECRET=... WORKER_BASE=https://meli-webhook...workers.dev \\
        python process_event.py [--dry-run] [--limit N] [--max-seconds 280] \\
        [--since 2026-05-23T00:00:00Z] [--topics orders_v2,orders]
"""
import os, sys, re, time, json, argparse, requests, psycopg2
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

DSN = os.environ["SUPABASE_DB_URL"]
WORKER_BASE = os.environ.get("WORKER_BASE", "https://meli-webhook.elite-market-1779161651.workers.dev").rstrip("/")
TOKEN_READ_SECRET = os.environ.get("TOKEN_READ_SECRET", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

PAID_STATUSES = {"paid", "partially_paid"}
DEAD_STATUSES = {"cancelled", "invalid"}  # no descontar


def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        print(f"[no telegram] {msg}"); return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass


_token_cache = {}
def get_token(account_upper):
    """Lee access_token vigente del Worker (autoridad central). Cachea por run."""
    if not account_upper:
        return None
    if account_upper in _token_cache:
        return _token_cache[account_upper]
    try:
        r = requests.get(f"{WORKER_BASE}/token/{account_upper}",
                         headers={"Authorization": f"Bearer {TOKEN_READ_SECRET}"}, timeout=30)
        if r.status_code == 200:
            tok = r.json().get("access_token")
            _token_cache[account_upper] = tok
            return tok
    except Exception as e:
        print(f"  token error {account_upper}: {str(e)[:120]}")
    _token_cache[account_upper] = None
    return None


def order_id_from_resource(resource, raw_payload):
    if resource:
        m = re.search(r'(\d{6,})', resource)
        if m:
            return m.group(1)
    if raw_payload:
        rp = raw_payload
        if isinstance(rp, str):
            try: rp = json.loads(rp)
            except: rp = {}
        m = re.search(r'(\d{6,})', (rp or {}).get("resource", "") or "")
        if m:
            return m.group(1)
    return None


def fetch_order(order_id, token):
    try:
        r = requests.get(f"https://api.mercadolibre.com/orders/{order_id}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=25)
        if r.status_code == 200:
            return r.json()
        return {"_http": r.status_code, "_body": r.text[:200]}
    except Exception as e:
        return {"_err": str(e)[:160]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="máx órdenes distintas a procesar (0=sin límite)")
    ap.add_argument("--max-seconds", type=int, default=280)
    ap.add_argument("--since", default=None, help="ISO ts: ignora órdenes con date_created anterior (watermark go-live)")
    ap.add_argument("--topics", default="orders_v2,orders")
    args = ap.parse_args()

    since_dt = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
        except Exception:
            print(f"⚠ --since inválido: {args.since}"); since_dt = None

    topics = tuple(t.strip() for t in args.topics.split(",") if t.strip())
    t0 = time.time()

    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()

    # Mapa user_id(seller) → (account_id, NICK_UPPER)
    cur.execute("SELECT id, nickname, meli_user_id FROM accounts WHERE active=true")
    by_user = {}
    for aid, nick, uid in cur.fetchall():
        if uid is not None:
            by_user[int(uid)] = (aid, (nick or "").upper())

    # Eventos pendientes de órdenes, agrupados por order_id (procesa el más antiguo)
    cur.execute(
        """
        SELECT id, resource, raw_payload, user_id, account_id, received_at
          FROM events
         WHERE topic = ANY(%s) AND processing_status = 'pending'
         ORDER BY id ASC
        """,
        (list(topics),)
    )
    rows = cur.fetchall()
    conn.commit()

    # Agrupa event_ids por order_id
    order_to_events = {}     # order_id -> [event_ids]
    order_meta = {}          # order_id -> (user_id, account_id)
    for ev_id, res, rp, uid, acc_id, rec in rows:
        oid = order_id_from_resource(res, rp)
        if not oid:
            continue
        order_to_events.setdefault(oid, []).append(ev_id)
        if oid not in order_meta:
            order_meta[oid] = (uid, acc_id)

    distinct_orders = list(order_to_events.keys())
    print(f"📥 eventos pending de órdenes: {len(rows)} | órdenes distintas: {len(distinct_orders)}")

    # Órdenes ya con movimiento 'sale' (idempotencia global)
    cur.execute("SELECT DISTINCT order_id FROM stock_movements WHERE order_id IS NOT NULL")
    already_sold = set(r[0] for r in cur.fetchall())
    conn.commit()

    stats = dict(sold=0, units=0, cogs=0.0, skip_already=0, skip_unpaid=0,
                 skip_cancelled=0, skip_unmapped=0, skip_notoken=0, oversell=0,
                 fetch_fail=0, events_done=0, orders_done=0)
    unmapped_samples = []
    oversell_samples = []

    # ---- Prefetch concurrente de órdenes (red en paralelo, DB serial) ----
    candidates = [oid for oid in distinct_orders if oid not in already_sold]
    if args.limit:
        candidates = candidates[:args.limit]

    def _resolve_nick(oid):
        uid, _ = order_meta[oid]
        if uid is not None and int(uid) in by_user:
            return by_user[int(uid)][1]
        return None

    def _prefetch(oid):
        nick = _resolve_nick(oid)
        tok = get_token(nick) if nick else None
        if not tok:
            return (oid, None)
        return (oid, fetch_order(oid, tok))

    order_cache = {}
    # warm el cache de tokens primero (serial, pocas cuentas) para evitar refresh duplicado
    for oid in candidates[:50]:
        nick = _resolve_nick(oid)
        if nick:
            get_token(nick)
    with ThreadPoolExecutor(max_workers=24) as ex:
        for oid, order in ex.map(_prefetch, candidates):
            order_cache[oid] = order
    print(f"🌐 órdenes pre-fetched: {sum(1 for v in order_cache.values() if v)}/{len(candidates)}")

    processed_order_count = 0
    for oid in distinct_orders:
        if args.limit and processed_order_count >= args.limit:
            break
        if time.time() - t0 > args.max_seconds:
            print("⏱ max-seconds alcanzado, corto aquí (re-run para continuar)")
            break
        processed_order_count += 1
        ev_ids = order_to_events[oid]
        uid, acc_id_evt = order_meta[oid]

        def mark_events(status, err=None):
            if args.dry_run:
                return
            cur.execute(
                "UPDATE events SET processing_status=%s, processed_at=now(), processing_error=%s "
                "WHERE id = ANY(%s)",
                (status, (err or None), ev_ids)
            )

        # 1) Idempotencia: ya vendida (go-live seed o run previo)
        if oid in already_sold:
            stats["skip_already"] += 1
            mark_events("done", "already_sold")
            conn.commit()
            continue

        # 2) Token de la cuenta vendedora
        acc_id, nick_upper = (None, None)
        if uid is not None and int(uid) in by_user:
            acc_id, nick_upper = by_user[int(uid)]
        if acc_id_evt:
            acc_id = acc_id_evt
        token = get_token(nick_upper) if nick_upper else None
        if not token:
            stats["skip_notoken"] += 1
            # NO marcamos done: queremos reintentar cuando haya token
            conn.commit()
            continue

        # 3) Orden (del prefetch concurrente; fallback a fetch directo)
        order = order_cache.get(oid)
        if order is None:
            order = fetch_order(oid, token)
        status = (order or {}).get("status")
        if not status:
            stats["fetch_fail"] += 1
            conn.commit()  # dejar pending para reintento
            continue
        if status in DEAD_STATUSES:
            stats["skip_cancelled"] += 1
            mark_events("done", f"order_{status}")
            conn.commit()
            continue
        if status not in PAID_STATUSES:
            stats["skip_unpaid"] += 1
            mark_events("done", f"order_{status}_noop")  # se re-evaluará en el webhook de pago (aún sin sale)
            conn.commit()
            continue

        # Watermark opcional
        if since_dt:
            dc = (order or {}).get("date_created")
            try:
                if dc and datetime.fromisoformat(dc.replace("Z", "+00:00")) < since_dt:
                    stats["skip_already"] += 1
                    mark_events("done", "before_watermark")
                    conn.commit()
                    continue
            except Exception:
                pass

        # 4) Procesar items
        items = (order or {}).get("order_items", []) or []
        order_ok = True
        order_units = 0
        order_cogs = 0.0
        for it in items:
            itm = it.get("item", {}) or {}
            mlm = itm.get("id")
            vid = itm.get("variation_id")
            qty = int(it.get("quantity") or 0)
            if not mlm or qty <= 0:
                continue
            cur.execute("SELECT sku, warehouse FROM resolve_sale_target(%s, %s)",
                        (mlm, int(vid) if vid else None))
            tgt = cur.fetchone()
            if not tgt or not tgt[0]:
                stats["skip_unmapped"] += 1
                if len(unmapped_samples) < 12:
                    unmapped_samples.append(f"{oid}:{mlm}/{vid} x{qty}")
                order_ok = False
                continue
            sku, wh = tgt

            if args.dry_run:
                order_units += qty
                # COGS estimado no se calcula en dry-run
                print(f"  [DRY] order {oid} {sku}@{wh} -{qty} (status={status})")
                continue

            # apply_stock_delta (lanza excepción si oversell)
            try:
                cur.execute(
                    "SELECT apply_stock_delta(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (sku, wh, -qty, 'sale', ev_ids[0], oid, mlm, acc_id,
                     'venta MELI (process_event)', 'process_event')
                )
                mov_id = cur.fetchone()[0]
            except psycopg2.Error as e:
                conn.rollback()
                stats["oversell"] += 1
                if len(oversell_samples) < 12:
                    oversell_samples.append(f"{oid}:{sku} x{qty}")
                # marca el evento con la razón pero no aborta el resto
                cur.execute(
                    "UPDATE events SET processing_status='error', processed_at=now(), processing_error=%s "
                    "WHERE id = ANY(%s)",
                    (f'oversell {sku}', ev_ids)
                )
                conn.commit()
                order_ok = False
                break

            # consume_cost (COGS)
            try:
                cur.execute("SELECT consume_cost(%s,%s,%s,%s,%s)", (sku, wh, qty, oid, mov_id))
                cogs = float(cur.fetchone()[0] or 0)
            except Exception as e:
                cogs = 0.0
                print(f"  ⚠ COGS falló {sku} order={oid}: {str(e)[:100]}")
            # Capturar precio de venta (revenue) en el stock_movement
            try:
                unit_price = it.get("unit_price")
                if unit_price is not None:
                    cur.execute("UPDATE stock_movements SET sale_price_mxn=%s WHERE id=%s",
                                (float(unit_price), mov_id))
            except Exception:
                pass
            order_units += qty
            order_cogs += cogs

        if args.dry_run:
            stats["sold"] += 1 if order_ok else 0
            stats["units"] += order_units
            continue

        if order_ok:
            mark_events("done")
            stats["sold"] += 1
            stats["units"] += order_units
            stats["cogs"] += order_cogs
            stats["orders_done"] += 1
            stats["events_done"] += len(ev_ids)
            conn.commit()
        else:
            # parcialmente no mapeada → marca skipped para no reintentar en loop infinito
            cur.execute(
                "UPDATE events SET processing_status='skipped', processed_at=now(), processing_error=%s "
                "WHERE id = ANY(%s)",
                ('unmapped_or_partial', ev_ids)
            )
            conn.commit()

    # Reporte
    lines = [
        ("🧪 *process_event DRY-RUN*" if args.dry_run else "⚙️ *process_event*"),
        f"Órdenes evaluadas: {processed_order_count}",
        f"Vendidas/descontadas: {stats['sold']} ({stats['units']} units)",
        (f"COGS registrado: ${stats['cogs']:,.2f}" if not args.dry_run else "COGS: (dry-run no calcula)"),
        f"Saltadas ya-vendidas: {stats['skip_already']}",
        f"Saltadas no-pagadas: {stats['skip_unpaid']}",
        f"Canceladas: {stats['skip_cancelled']}",
        f"Sin mapear (SKU): {stats['skip_unmapped']}",
        f"Sin token: {stats['skip_notoken']}",
        f"Oversell: {stats['oversell']}",
        f"Fetch fail: {stats['fetch_fail']}",
    ]
    if unmapped_samples:
        lines.append("Unmapped ej: " + ", ".join(unmapped_samples[:8]))
    if oversell_samples:
        lines.append("Oversell ej: " + ", ".join(oversell_samples[:8]))
    msg = "\n".join(lines)
    print("\n" + msg)
    if not args.dry_run and (stats["sold"] or stats["oversell"]):
        tg(msg)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
