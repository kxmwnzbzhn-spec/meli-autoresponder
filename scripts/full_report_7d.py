"""Reporte 7d: piezas vendidas + reclamos abiertos + neto por cuenta."""
import os, requests
from datetime import datetime, timezone, timedelta

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
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

now = datetime.now(timezone.utc)
date_from = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"📊 REPORTE 7d ({date_from[:10]} → hoy)\n")

per_account = {}
totals = {"orders":0, "units":0, "gross":0.0, "fees":0.0, "ship":0.0, "refunds":0.0,
          "net":0.0, "claims_open":0, "cancelled":0, "returns_active":0}

for label, env in ACCOUNTS:
    rt = os.environ.get(env, "")
    a = {"orders":0, "units":0, "gross":0.0, "fees":0.0, "ship":0.0, "refunds":0.0,
         "net":0.0, "claims_open":0, "cancelled":0, "returns_active":0}
    if not rt:
        per_account[label] = a; print(f"[{label}] sin token"); continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt
        }, timeout=15).json()
        tok = r.get("access_token")
        if not tok:
            per_account[label] = a; print(f"[{label}] oauth fail"); continue
        H = {"Authorization": f"Bearer {tok}"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        uid = me["id"]
    except Exception as e:
        per_account[label] = a; print(f"[{label}] err {e}"); continue

    # Orders 7d
    off = 0
    while True:
        url = f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={off}&sort=date_desc"
        rr = requests.get(url, headers=H, timeout=20).json()
        results = rr.get("results", [])
        if not results: break
        for o in results:
            st = o.get("status","")
            amt = float(o.get("total_amount", 0) or 0)
            for oi in o.get("order_items", []):
                a["units"] += oi.get("quantity", 0) or 0
            if st == "cancelled": a["cancelled"] += 1; continue
            if st not in ("paid","shipped","delivered","handling","ready_to_ship"): continue
            a["orders"] += 1
            a["gross"] += amt
            try:
                od = requests.get(f"https://api.mercadolibre.com/orders/{o['id']}", headers=H, timeout=10).json()
                for pay in od.get("payments", []):
                    if pay.get("status") == "approved":
                        a["fees"] += float(pay.get("marketplace_fee", 0) or 0)
                    a["refunds"] += float(pay.get("transaction_amount_refunded", 0) or 0)
                sh_id = (od.get("shipping") or {}).get("id")
                if sh_id:
                    sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}", headers=H, timeout=10).json()
                    so = sd.get("shipping_option", {}) or {}
                    a["ship"] += float(so.get("list_cost", 0) or 0)
            except Exception:
                pass
        if len(results) < 50: break
        off += 50
        if off > 5000: break

    # Claims abiertos
    try:
        c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?stage=claim&status=opened&limit=50", headers=H, timeout=10).json()
        a["claims_open"] = len(c.get("data", []) or [])
    except: pass

    # Returns activas (return type)
    try:
        c2 = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?type=return&status=opened&limit=50", headers=H, timeout=10).json()
        a["returns_active"] = len(c2.get("data", []) or [])
    except: pass

    a["net"] = a["gross"] - a["fees"] - a["ship"] - a["refunds"]
    per_account[label] = a
    for k in totals: totals[k] += a[k]
    print(f"[{label}] {a['orders']:>4} ord | {a['units']:>4} u | bruto ${a['gross']:>9,.0f} -fee${a['fees']:>5,.0f} -ship${a['ship']:>5,.0f} -ref${a['refunds']:>5,.0f} = NET${a['net']:>9,.0f} | claims:{a['claims_open']} returns:{a['returns_active']} cancel:{a['cancelled']}")

print(f"\n========= TOTAL 7 DÍAS =========")
print(f"  Órdenes:        {totals['orders']}")
print(f"  Unidades:       {totals['units']}")
print(f"  Bruto:          ${totals['gross']:>12,.0f}")
print(f"  -Comisiones:    ${totals['fees']:>12,.0f}")
print(f"  -Envíos seller: ${totals['ship']:>12,.0f}")
print(f"  -Devoluciones:  ${totals['refunds']:>12,.0f}")
print(f"  ─────────────────────────")
print(f"  NET:            ${totals['net']:>12,.0f}")
print(f"  Canceladas:     {totals['cancelled']}")
print(f"  Claims abiertos: {totals['claims_open']}")
print(f"  Returns activas: {totals['returns_active']}")

# Telegram
tg_t = os.environ.get("TELEGRAM_BOT_TOKEN"); tg_c = os.environ.get("TELEGRAM_CHAT_ID")
if tg_t and tg_c:
    lines = ["📊 <b>REPORTE 7 DÍAS</b>", ""]
    for acc, d in sorted(per_account.items(), key=lambda x:-x[1]["net"]):
        if d["orders"] > 0 or d["claims_open"] > 0:
            lines.append(f"<b>{acc}</b>: {d['units']}u / ${d['gross']:,.0f} → <b>${d['net']:,.0f}</b> NET | claims:{d['claims_open']}")
    lines += ["", "━━━━━━━━━━━━━━━━",
              f"<b>Total piezas:</b> {totals['units']}",
              f"<b>Reclamos activos:</b> {totals['claims_open']}",
              f"Bruto: ${totals['gross']:,.0f}",
              f"-Fees: ${totals['fees']:,.0f}",
              f"-Envíos: ${totals['ship']:,.0f}",
              f"-Devolus: ${totals['refunds']:,.0f}",
              f"<b>NET 7d: ${totals['net']:,.0f}</b>"]
    requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage",
        data={"chat_id":tg_c, "text":"\n".join(lines), "parse_mode":"HTML"}, timeout=10)
    print("\nTG sent")
