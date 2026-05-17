"""Dump SKUs + precio venta promedio MELI para que el user estime costos.

Genera un CSV con todos los SKUs únicos, su nombre/marca/línea, y el precio
de venta promedio actual en MELI. Sirve como punto de partida para que el
user llene la columna `unit_cost_mxn` del stock_seed.csv mañana.

Output:
    stdout: CSV completo
    /tmp/skus_for_costing.csv: archivo
    GH Actions artifact: skus-for-costing (descargable desde Actions UI)
"""
import os, sys, csv, psycopg2

DSN = os.environ["SUPABASE_DB_URL"]

conn = psycopg2.connect(DSN)
cur = conn.cursor()

cur.execute(
    """
    SELECT
        p.sku,
        p.modelo,
        p.color,
        p.brand,
        p.line,
        p.condition,
        p.alert_threshold,
        COUNT(DISTINCT l.mlm_id) AS n_listings,
        ROUND(AVG(l.price)::numeric, 2) AS avg_price_mxn,
        MIN(l.price) AS min_price_mxn,
        MAX(l.price) AS max_price_mxn,
        ROUND((AVG(l.price) * 0.65)::numeric, 2) AS suggested_cost_at_35pct_margin,
        ROUND((AVG(l.price) * 0.55)::numeric, 2) AS suggested_cost_at_45pct_margin
    FROM products p
    LEFT JOIN listings l ON l.sku = p.sku AND l.status = 'active'
    WHERE p.archived = false
    GROUP BY p.sku, p.modelo, p.color, p.brand, p.line, p.condition, p.alert_threshold
    ORDER BY p.brand NULLS LAST, p.modelo, p.color
    """
)
rows = cur.fetchall()

headers = [
    "sku", "modelo", "color", "brand", "line", "condition", "alert_threshold",
    "n_listings", "avg_price_mxn", "min_price_mxn", "max_price_mxn",
    "suggested_cost_at_35pct_margin", "suggested_cost_at_45pct_margin",
    # Columnas que TÚ llenarás mañana:
    "unit_cost_mxn_REAL", "physical_count",
]

# Stdout
w = csv.writer(sys.stdout)
w.writerow(headers)
for r in rows:
    w.writerow(list(r) + ["", ""])

# Archivo para artifact upload
out_path = "/tmp/skus_for_costing.csv"
with open(out_path, "w", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(headers)
    for r in rows:
        w.writerow(list(r) + ["", ""])

print(f"\n--- {len(rows)} SKUs exportados a {out_path} ---", file=sys.stderr)

cur.close()
conn.close()
