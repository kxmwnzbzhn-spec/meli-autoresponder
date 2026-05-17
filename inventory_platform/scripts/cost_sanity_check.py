"""Sanity check cost_layers diario.

Corre la función SQL cost_layers_sanity_check() (definida en 03_procurement_cost_functions.sql)
y alerta vía Telegram si encuentra inconsistencias.

Detecta:
  - qty_restante_overflow: capa con qty_restante > qty_recibida
  - stock_sin_costed: stock físico sin cost_layer activo que lo respalde
  - po_received_no_layer: PO recibida sin cost_layer asociada

Uso:
    SUPABASE_DB_URL=... TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... \\
        python cost_sanity_check.py
"""
import os, sys, requests, psycopg2

DSN = os.environ["SUPABASE_DB_URL"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")


def tg(msg: str) -> None:
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


conn = psycopg2.connect(DSN)
cur = conn.cursor()

try:
    cur.execute("SELECT issue, sku, warehouse, layer_id, detail FROM cost_layers_sanity_check()")
    rows = cur.fetchall()

    if not rows:
        print("✓ Cost layers sanity check: 0 issues")
        sys.exit(0)

    print(f"⚠ {len(rows)} issues detectados:")

    # Agrupar por tipo
    by_type = {}
    for issue, sku, wh, layer_id, detail in rows:
        by_type.setdefault(issue, []).append((sku, wh, layer_id, detail))

    summary_lines = ["🚨 *Cost layers sanity issues*", ""]
    for issue_type, items in by_type.items():
        summary_lines.append(f"*{issue_type}*: {len(items)} casos")
        for sku, wh, layer_id, detail in items[:5]:  # primeros 5 por tipo
            sku_str = sku or "—"
            wh_str = wh or "—"
            summary_lines.append(f"  • `{sku_str}` / `{wh_str}` → {detail}")
        if len(items) > 5:
            summary_lines.append(f"  ... y {len(items) - 5} más")
        summary_lines.append("")

    summary_lines.append("Resolver con `manual_adjustments` o investigar capa especifica.")
    msg = "\n".join(summary_lines)
    print(msg)
    tg(msg)

    # Exit code != 0 para que GH Actions marque rojo
    sys.exit(1)

finally:
    cur.close()
    conn.close()
