"""Go-live seed — reconciliación stock físico contra órdenes pendientes.

Inputs:
  - CSV con conteo físico: inventory_platform/data/stock_seed.csv
    Columnas: sku,warehouse,physical_count,unit_cost_mxn
  - snapshot_batch UUID (default: latest)

Flujo transaccional:
  1. Para cada (sku, warehouse) en CSV:
     a. INSERT cost_layer (source_type='opening_balance', qty=physical_count, costo=unit_cost_mxn)
     b. apply_stock_delta(+physical_count, type='initial_seed', reason='Go-live count YYYY-MM-DD')
  2. Para cada pending_orders_snapshot row WHERE applied_to_stock=false AND batch=target:
     a. movement_id = apply_stock_delta(-qty, type='sale', order_id=...)
     b. consume_cost(sku, warehouse, qty, order_id, movement_id) -- registra COGS
     c. UPDATE row SET applied=true, applied_movement_id=movement_id

Resultado final:
    stock.qty = physical_count - SUM(pending_qty)
    = lo realmente disponible para vender

Uso:
    SUPABASE_DB_URL=... python go_live_seed.py \\
        [--csv inventory_platform/data/stock_seed.csv] \\
        [--batch latest|<uuid>] \\
        [--warehouse-default bodega_main] \\
        [--dry-run]
"""
import os, sys, csv, argparse, psycopg2, requests

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="inventory_platform/data/stock_seed.csv")
parser.add_argument("--batch", default="latest",
                    help="UUID del snapshot batch a aplicar, o 'latest'")
parser.add_argument("--warehouse-default", default="bodega_main")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

DSN = os.environ["SUPABASE_DB_URL"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")


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
    except Exception:
        pass


if not os.path.exists(args.csv):
    print(f"✗ CSV no existe: {args.csv}")
    sys.exit(1)

conn = psycopg2.connect(DSN)
conn.autocommit = False
cur = conn.cursor()

try:
    # 1. Resolver batch
    if args.batch == "latest":
        cur.execute("SELECT snapshot_batch FROM pending_orders_snapshot ORDER BY snapshot_ts DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("⚠ No hay snapshots. ¿Corriste inv_snapshot_pending_orders?")
            # Seguimos — quizá quieres seedear sin pending orders (sistema fresco)
            batch = None
        else:
            batch = row[0]
    else:
        batch = args.batch

    print(f"📦 Snapshot batch: {batch}")

    # 2. Validar que el batch no se haya aplicado
    if batch:
        cur.execute(
            "SELECT COUNT(*), COUNT(*) FILTER (WHERE applied_to_stock=true) "
            "FROM pending_orders_snapshot WHERE snapshot_batch=%s",
            (batch,)
        )
        total, applied = cur.fetchone()
        print(f"  batch tiene {total} órdenes, {applied} ya aplicadas")
        if applied == total and total > 0:
            print("⚠ Este batch YA fue aplicado completo. ¿Doble run?")
            sys.exit(1)

    # 3. Leer CSV stock físico
    seed_rows = []
    with open(args.csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            sku = (r.get("sku") or "").strip()
            if not sku or sku.startswith("#"):
                continue
            wh = (r.get("warehouse") or args.warehouse_default).strip()
            try:
                qty = int(r.get("physical_count") or 0)
                cost = float(r.get("unit_cost_mxn") or 0)
            except ValueError:
                print(f"  ⚠ row inválido (skip): {r}")
                continue
            if qty < 0:
                continue
            seed_rows.append((sku, wh, qty, cost))

    print(f"📦 SKUs a seedear: {len(seed_rows)}")
    if not seed_rows:
        print("✗ CSV vacío o sin rows válidas")
        sys.exit(1)

    total_physical = sum(qty for _, _, qty, _ in seed_rows)

    # 4. Seed inicial: cost_layer + initial_seed movement
    seeded = 0
    for sku, wh, qty, cost in seed_rows:
        if qty == 0:
            # SKU contado pero 0 unidades — registra cost_layer placeholder cero? No, skip layer pero registra movement
            if not args.dry_run:
                cur.execute(
                    "SELECT apply_stock_delta(%s,%s,%s,%s, NULL, NULL, NULL, NULL, %s, %s)",
                    (sku, wh, 0, 'initial_seed', 'Go-live count: 0 units found', 'go_live_seed')
                )
            print(f"  · {sku} @ {wh}: 0 units (no layer)")
            continue

        if args.dry_run:
            print(f"  [DRY] {sku} @ {wh}: +{qty} units @ ${cost:.2f}/unit")
            seeded += 1
            continue

        # Cost layer
        cur.execute(
            """
            INSERT INTO cost_layers
                (sku, warehouse, source_type, source_id, qty_recibida, qty_restante,
                 costo_unitario_base_mxn, fletes_prorrateados_mxn, otros_prorrateados_mxn)
            VALUES (%s, %s, 'opening_balance', NULL, %s, %s, %s, 0, 0)
            """,
            (sku, wh, qty, qty, cost)
        )

        # Stock movement
        cur.execute(
            "SELECT apply_stock_delta(%s,%s,%s,%s, NULL, NULL, NULL, NULL, %s, %s)",
            (sku, wh, qty, 'initial_seed', f'Go-live count: {qty} units @ ${cost:.2f}', 'go_live_seed')
        )
        seeded += 1
        print(f"  ✓ {sku} @ {wh}: +{qty} units @ ${cost:.2f}/u")

    print(f"\n→ Seed inicial: {seeded} SKUs / {total_physical} units")

    # 5. Aplicar pending orders del batch
    pending_applied = 0
    pending_skipped = 0
    cogs_total = 0.0

    if batch:
        cur.execute(
            """
            SELECT id, order_id, mlm_id, sku, qty, account_id, total_amount
              FROM pending_orders_snapshot
             WHERE snapshot_batch = %s
               AND applied_to_stock = false
             ORDER BY date_paid ASC, id ASC
            """,
            (batch,)
        )
        pending = cur.fetchall()
        print(f"\n📋 Pending orders en batch: {len(pending)}")

        for row_id, order_id, mlm_id, sku, qty, account_id, total_amount in pending:
            if not sku:
                # Orden no mapeada a un SKU — skip con razón
                if not args.dry_run:
                    cur.execute(
                        "UPDATE pending_orders_snapshot SET skip_reason=%s WHERE id=%s",
                        ('sku_no_mapeado', row_id)
                    )
                pending_skipped += 1
                print(f"  ⚠ skip order {order_id} mlm={mlm_id} qty={qty} — SKU no mapeado")
                continue

            if args.dry_run:
                print(f"  [DRY] order {order_id} {sku} -{qty}")
                pending_applied += 1
                continue

            # apply_stock_delta para esta venta
            try:
                cur.execute(
                    "SELECT apply_stock_delta(%s,%s,%s,%s, NULL, %s, %s, %s, %s, %s)",
                    (sku, args.warehouse_default, -qty, 'sale',
                     order_id, mlm_id, account_id,
                     f'go-live retroactivo: snapshot batch {str(batch)[:8]}',
                     'go_live_seed')
                )
                mov_id = cur.fetchone()[0]
            except psycopg2.errors.RaiseException as e:
                # OVERSELL — no había suficiente físico para cubrir esta orden
                err = str(e)[:200]
                if not args.dry_run:
                    cur.execute("ROLLBACK TO SAVEPOINT before_pending") if False else None
                cur.execute(
                    "UPDATE pending_orders_snapshot SET skip_reason=%s WHERE id=%s",
                    (f'oversell: {err}', row_id)
                )
                pending_skipped += 1
                print(f"  ⚠ OVERSELL para {sku} order={order_id} qty={qty}: {err}")
                continue

            # consume_cost — registra COGS
            try:
                cur.execute(
                    "SELECT consume_cost(%s,%s,%s,%s,%s)",
                    (sku, args.warehouse_default, qty, order_id, mov_id)
                )
                cogs = float(cur.fetchone()[0] or 0)
                cogs_total += cogs
            except Exception as e:
                # COGS opcional — si falla, no abortamos (stock ya decrementó)
                cogs = 0.0
                print(f"  ⚠ COGS falló para {sku} order={order_id}: {str(e)[:100]}")

            # Marca aplicada
            cur.execute(
                """
                UPDATE pending_orders_snapshot
                   SET applied_to_stock=true,
                       applied_at=now(),
                       applied_movement_id=%s
                 WHERE id=%s
                """,
                (mov_id, row_id)
            )
            pending_applied += 1

    if args.dry_run:
        print("\n[DRY RUN] No se commiteó nada")
        conn.rollback()
    else:
        conn.commit()

    # 6. Reporte final
    cur.execute("SELECT COUNT(*), SUM(qty) FROM stock WHERE qty > 0")
    n_stock_rows, total_stock = cur.fetchone()

    summary = [
        f"🟢 *Go-live seed completado*",
        f"Batch: `{str(batch)[:8] if batch else 'sin pending'}`",
        f"",
        f"*Inputs:*",
        f"  • Stock físico contado: {seeded} SKUs / {total_physical} units",
        f"  • Pending orders aplicadas: {pending_applied} órdenes",
        f"  • Pending skipped: {pending_skipped} (SKU no mapeado u oversell)",
        f"  • COGS retroactivo registrado: ${cogs_total:,.2f} MXN",
        f"",
        f"*Estado actual DB:*",
        f"  • Filas stock: {n_stock_rows}",
        f"  • Total units disponibles: {total_stock or 0}",
        f"  • Diferencia (físico − pendiente): {total_physical - sum(p[4] for p in (pending or []) if p[3]) if batch else total_physical}",
        f"",
        f"✅ Sistema listo. Habilita Worker MELI y procesa ventas nuevas.",
    ]
    msg = "\n".join(summary)
    print("\n" + msg)
    if not args.dry_run:
        tg(msg)

except Exception as e:
    conn.rollback()
    err_msg = f"✗ Go-live seed FALLÓ: {e}"
    print(err_msg)
    tg(f"🚨 {err_msg}")
    sys.exit(1)
finally:
    cur.close()
    conn.close()
