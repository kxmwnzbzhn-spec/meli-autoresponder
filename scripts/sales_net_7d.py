#!/usr/bin/env python3
"""Ventas NET últimos 7 días por cuenta:
   net = bruto - marketplace_fee - shipping_seller_cost - refunds
"""
import os, requests
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
    ("BREN", "MELI_REFRESH_TOKEN_BREN"),
    ("YC_NEW", "MELI_REFRESH_TOKEN_YC_NEW"),
    ("WILBERT", "MELI_REFRESH_TOKEN_WILBERT"),
]

now_utc = datetime.now(timezone.utc)
date_from = (now_utc - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
date_to = now_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"📊 NETO ÚLTIMOS 7 DÍAS — {date_from[:10]} a {date_to[:10]} UTC\n")

per_account = {}
totals = {"orders":0, "gross":0, "fees":0, "ship":0, "refunds":0, "net":0, "cancelled":0, "qty":0}

for label, env in ACCOUNTS:
    RT = os.environ.get(env, "")
    if not RT:
        print(f"[{label}] sin token, skip")
        continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }, timeout=15).json()
        tok = r.get("access_token")
        if not tok:
            print(f"[{label}] oauth fail")
            continue
        H = {"Authorization": f"Bearer {tok}"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        UID = me["id"]
    except Exception as e:
        print(f"[{label}] err: {e}")
        continue

    a = {"orders":0, "gross":0, "fees":0, "ship":0, "refunds":0, "net":0, "cancelled":0, "qty":0}
    offset = 0
    while True:
        url = f"https://api.mercadolibre.com/orders/search?seller={UID}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50&offset={offset}&sort=date_desc"
        rr = requests.get(url, headers=H, timeout=20).json()
        results = rr.get("results", [])
        if not results: break
        for o in results:
            st = o.get("status","")
            amt = float(o.get("total_amount", 0) or 0)
            for oi in o.get("order_items", []):
                a["qty"] += oi.get("quantity", 0) or 0

            if st == "cancelled":
                a["cancelled"] += 1
                # Si es cancelada, no se cuenta ingreso (no impacta net)
                continue
            if st not in ("paid","shipped","delivered","handling","ready_to_ship"):
                continue

            a["orders"] += 1
            a["gross"] += amt

            # Detail call para fees + shipping + refunds
            order_id = o.get("id")
            try:
                od = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=H, timeout=10).json()
                for pay in od.get("payments", []):
                    if pay.get("status") == "approved":
                        a["fees"] += float(pay.get("marketplace_fee", 0) or 0)
                    # transaction_amount_refunded captura devoluciones parciales o totales
                    a["refunds"] += float(pay.get("transaction_amount_refunded", 0) or 0)

                sh_id = (od.get("shipping") or {}).get("id")
                if sh_id:
                    sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}", headers=H, timeout=10).json()
                    so = sd.get("shipping_option", {}) or {}
                    a["ship"] += float(so.get("list_cost", 0) or 0)
            except Exception:
                pass
        if len(results) < 50: break
        offset += 50
        if offset > 5000: break

    a["net"] = a["gross"] - a["fees"] - a["ship"] - a["refunds"]
    per_account[label] = a
    for k in totals: totals[k] += a[k]
    print(f"[{label}] {a['orders']:>4} ord | {a['qty']:>5} u | bruto ${a['gross']:>10,.0f} | -fees ${a['fees']:>7,.0f} | -ship ${a['ship']:>7,.0f} | -refunds ${a['refunds']:>7,.0f} | NET ${a['net']:>10,.0f} | cancel {a['cancelled']}")

print(f"\n========================================")
print(f"TOTAL 7d:")
print(f"  Bruto:      ${totals['gross']:>12,.0f} ({totals['orders']} órdenes, {totals['qty']} unidades)")
print(f"  Comisiones: -${totals['fees']:>11,.0f}")
print(f"  Envíos:     -${totals['ship']:>11,.0f}")
print(f"  Devolucs:   -${totals['refunds']:>11,.0f}")
print(f"  ----------------------------------------")
print(f"  NET:         ${totals['net']:>12,.0f}")
print(f"  Cancelled:   {totals['cancelled']}")

# Telegram
tg_t = os.environ.get("TELEGRAM_BOT_TOKEN")
tg_c = os.environ.get("TELEGRAM_CHAT_ID")
if tg_t and tg_c:
    lines = ["📊 <b>VENTAS NETO ÚLTIMOS 7 DÍAS</b>", ""]
    for acc, d in sorted(per_account.items(), key=lambda x: -x[1]["net"]):
        if d["orders"] > 0:
            lines.append(f"<b>{acc}</b>: {d['orders']} ord / ${d['gross']:,.0f} bruto → <b>${d['net']:,.0f}</b> NET")
    lines.append("")
    lines.append(f"<b>━━━━━━━━━━━━━━━━━━━━</b>")
    lines.append(f"Bruto:    ${totals['gross']:,.0f}")
    lines.append(f"-Fees:    -${totals['fees']:,.0f}")
    lines.append(f"-Envíos:  -${totals['ship']:,.0f}")
    lines.append(f"-Devolus: -${totals['refunds']:,.0f}")
    lines.append(f"<b>NET 7d:   ${totals['net']:,.0f}</b>")
    lines.append(f"({totals['orders']} órdenes / {totals['qty']} u / {totals['cancelled']} canceladas)")
    msg = "\n".join(lines)
    requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage",
        data={"chat_id":tg_c, "text":msg, "parse_mode":"HTML"}, timeout=10)
    print("\nTG sent")
