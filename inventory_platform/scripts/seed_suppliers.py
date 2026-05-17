"""Seed suppliers desde CSV.

Lee inventory_platform/data/suppliers_seed.csv y hace upsert a la tabla suppliers.
NO sobrescribe registros existentes (ON CONFLICT code DO NOTHING) para preservar
ediciones manuales.

CSV format:
    code,razon_social,rfc,contacto_nombre,contacto_email,contacto_telefono,
    banco_nombre,banco_cuenta,banco_clabe,divisa_default,dias_credito,pais,notas

Uso:
    SUPABASE_DB_URL=... python seed_suppliers.py [path/to/csv]
    (path default: inventory_platform/data/suppliers_seed.csv)
"""
import os, sys, csv, psycopg2

DSN = os.environ["SUPABASE_DB_URL"]
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "inventory_platform/data/suppliers_seed.csv"

if not os.path.exists(CSV_PATH):
    print(f"✗ CSV no encontrado: {CSV_PATH}")
    sys.exit(1)

conn = psycopg2.connect(DSN)
conn.autocommit = False
cur = conn.cursor()

inserted = 0
skipped = 0
errors = []

try:
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # row 1 = header
            code = (row.get("code") or "").strip()
            razon = (row.get("razon_social") or "").strip()
            if not code or not razon:
                errors.append(f"row {i}: code o razon_social vacíos, skip")
                continue
            try:
                cur.execute(
                    """
                    INSERT INTO suppliers
                        (code, razon_social, rfc, contacto_nombre, contacto_email, contacto_telefono,
                         banco_nombre, banco_cuenta, banco_clabe, divisa_default, dias_credito, pais, notas)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (code) DO NOTHING
                    RETURNING id
                    """,
                    (
                        code,
                        razon,
                        (row.get("rfc") or None) or None,
                        (row.get("contacto_nombre") or None) or None,
                        (row.get("contacto_email") or None) or None,
                        (row.get("contacto_telefono") or None) or None,
                        (row.get("banco_nombre") or None) or None,
                        (row.get("banco_cuenta") or None) or None,
                        (row.get("banco_clabe") or None) or None,
                        (row.get("divisa_default") or "MXN")[:3].upper(),
                        int(row.get("dias_credito") or 0),
                        (row.get("pais") or "MX")[:2].upper(),
                        (row.get("notas") or None) or None,
                    ),
                )
                if cur.fetchone():
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(f"row {i} ({code}): {e}")
                conn.rollback()
                cur = conn.cursor()
                continue

    conn.commit()
    print(f"✓ Suppliers seeded: {inserted} insertados, {skipped} ya existían")
    if errors:
        print(f"⚠ {len(errors)} errores:")
        for e in errors[:20]:
            print(f"  - {e}")
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
    sys.exit(1)
finally:
    cur.close()
    conn.close()
