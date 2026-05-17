"""Seed opening_balance cost_layers para que consume_cost() funcione día 1.

Para cada (sku, warehouse) en stock con qty>0 y SIN cost_layer activo,
crea una capa source_type='opening_balance' con costo estimado.

Fuente del costo (en orden de prioridad):
  1. CSV explícito: inventory_platform/data/opening_balance.csv (sku,warehouse,unit_cost_mxn)
  2. Argumento --default-cost N (aplica a SKUs sin entrada en CSV)
  3. Si no se especifica nada → SKIP (no crea capa, alertará luego)

Uso:
    SUPABASE_DB_URL=... python seed_opening_balance.py \\
        [--csv path/to/opening_balance.csv] \\
        [--default-cost 100.00] \\
        [--dry-run]
"""
import os, sys, csv, argparse, psycopg2

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="inventory_platform/data/opening_balance.csv")
parser.add_argument("--default-cost", type=float, default=None,
                    help="Costo MXN por defecto para SKUs sin entrada en CSV")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

DSN = os.environ["SUPABASE_DB_URL"]

# Cargar overrides del CSV
overrides = {}  # (sku, warehouse) -> unit_cost_mxn
if os.path.exists(args.csv):
    with open(args.csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = (row.get("sku") or "").strip()
            wh = (row.get("warehouse") or "bodega_main").strip()
            try:
                cost = float(row.get("unit_cost_mxn") or 0)
            except ValueError:
                continue
            if sku and cost > 0:
                overrides[(sku, wh)] = cost
    print(f"✓ Cargados {len(overrides)} overrides de {args.csv}")
else:
    print(f"⚠ CSV no encontrado: {args.csv} (continúa sólo con --default-cost si se proporcionó)")

conn = psycopg2.connect(DSN)
conn.autocommit = False
cur = conn.cursor()

try:
    # Encontrar (sku, warehouse) con stock>0 SIN cost_layer activo
    cur.execute(
        """
        SELECT s.sku, s.warehouse, s.qty
          FROM stock s
         WHERE s.qty > 0
           AND NOT EXISTS (
               SELECT 1 FROM cost_layers cl
                WHERE cl.sku = s.sku
                  AND cl.warehouse = s.warehouse
                  AND cl.qty_restante > 0
                  AND cl.archived = false
           )
        ORDER BY s.sku, s.warehouse
        """
    )
    rows = cur.fetchall()
    print(f"📦 {len(rows)} (sku,warehouse) con stock sin costeo")

    created = 0
    skipped_no_cost = 0
    for sku, wh, qty in rows:
        cost = overrides.get((sku, wh))
        if cost is None and args.default_cost is not None:
            cost = args.default_cost
        if cost is None:
            skipped_no_cost += 1
            continue

        if args.dry_run:
            print(f"  [DRY] would seed {sku} {wh} qty={qty} cost={cost:.2f}")
            created += 1
            continue

        cur.execute(
            """
            INSERT INTO cost_layers
                (sku, warehouse, source_type, source_id, qty_recibida, qty_restante,
                 costo_unitario_base_mxn, fletes_prorrateados_mxn, otros_prorrateados_mxn)
            VALUES (%s, %s, 'opening_balance', NULL, %s, %s, %s, 0, 0)
            """,
            (sku, wh, qty, qty, cost)
        )
        created += 1

    if not args.dry_run:
        conn.commit()
    print(f"{'(dry-run) ' if args.dry_run else ''}✓ Capas seeded: {created}")
    if skipped_no_cost:
        print(f"⚠ {skipped_no_cost} (sku,warehouse) sin costo conocido — NO seeded")
        print("  → Para resolver: agrega entries al CSV o usa --default-cost N")
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
    sys.exit(1)
finally:
    cur.close()
    conn.close()
