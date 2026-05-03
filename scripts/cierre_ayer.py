#!/usr/bin/env python3
"""Cierre del 2 de mayo 2026 — Raymundo + Juan
Pulls /orders/search filtered by date_closed yesterday + cuenta.
Computes gross, comision MELI, envio, neto y ranking por modelo.
"""
import os, requests, json
from datetime import datetime, timedelta, timezone

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

ACCS = {
    "Raymundo": os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"],
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
}

# CDMX = UTC-6
TZ = timezone(timedelta(hours=-6))
TODAY  = datetime.now(TZ).date()
TARGET = TODAY - timedelta(days=1)   # Ayer = 2 de mayo
START  = datetime(TARGET.year, TARGET.month, TARGET.day, 0,0,0, tzinfo=TZ)
END    = START + timedelta(days=1)
print(f"Target day: {TARGET}  [{START.isoformat()} → {END.isoformat()}]")

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r["access_token"]

def fetch_orders(H, uid):
    orders = []
    offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search",
                         headers=H,
                         params={"seller": uid,
                                 "order.date_created.from": START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                 "order.date_created.to":   END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                 "limit":50, "offset":offset},
                         timeout=20).json()
        results = r.get("results",[])
        if not results: break
        orders.extend(results)
        offset += len(results)
        total = r.get("paging",{}).get("total",0)
        if offset >= total: break
    return orders

summary = {}
for name, rt in ACCS.items():
    if not rt:
        print(f"\n{name}: sin refresh_token, skip")
        continue
    print(f"\n=== {name} ===")
    H = {"Authorization": f"Bearer {tok(rt)}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
    uid = me["id"]
    print(f"  uid={uid} nick={me.get('nickname')}")
    orders = fetch_orders(H, uid)
    paid = [o for o in orders if o.get("status") == "paid"]
    cancelled = [o for o in orders if o.get("status") == "cancelled"]

    gross = 0.0
    comision = 0.0
    units = 0
    by_model = {}
    for o in paid:
        for it in o.get("order_items", []):
            qty = it.get("quantity",1)
            unit_price = float(it.get("unit_price",0) or 0)
            sale_fee = float(it.get("sale_fee", 0) or 0)
            line = unit_price * qty
            line_fee = sale_fee * qty
            gross += line
            comision += line_fee
            units += qty
            title = (it.get("item",{}).get("title","") or "").lower()
            if "go 4" in title or "go4" in title: m = "Go 4"
            elif "go 3" in title or "go3" in title: m = "Go 3"
            elif "clip 5" in title or "clip5" in title: m = "Clip 5"
            elif "charge" in title: m = "Charge 6"
            elif "flip" in title: m = "Flip 7"
            elif "grip" in title: m = "Grip"
            else: m = "Otros"
            by_model[m] = by_model.get(m,{"u":0,"$":0.0})
            by_model[m]["u"] += qty
            by_model[m]["$"] += line

    # Envíos pagados por seller (solo si seller_pays)
    envios = 0.0
    for o in paid:
        sh = o.get("shipping",{}) or {}
        cost = sh.get("cost") or 0
        envios += float(cost or 0)

    neto = gross - comision - envios
    summary[name] = {
        "ordenes": len(paid),
        "canceladas": len(cancelled),
        "u": units,
        "bruto": gross,
        "comision": comision,
        "envios": envios,
        "neto": neto,
        "by_model": by_model,
    }
    print(f"  paid={len(paid)} cancelled={len(cancelled)} u={units}")
    print(f"  bruto=${gross:,.0f} comision=${comision:,.0f} envios=${envios:,.0f} NETO=${neto:,.0f}")
    for m, d in sorted(by_model.items(), key=lambda x: -x[1]["$"]):
        print(f"    {m}: {d['u']}u  ${d['$']:,.0f}")

# Telegram summary
if TG and TGCID:
    msg = f"📊 *Cierre {TARGET.strftime('%d/%m/%Y')}*\n\n"
    total_neto = 0
    total_u = 0
    for name, s in summary.items():
        msg += f"*{name}*\n"
        msg += f"  • Ventas: *{s['ordenes']}* / {s['u']}u\n"
        msg += f"  • Bruto: ${s['bruto']:,.0f}\n"
        msg += f"  • Comisión MELI: -${s['comision']:,.0f}\n"
        msg += f"  • Envíos: -${s['envios']:,.0f}\n"
        msg += f"  • *NETO: ${s['neto']:,.0f}*\n"
        if s.get("canceladas"):
            msg += f"  • Canceladas: {s['canceladas']}\n"
        for m, d in sorted(s["by_model"].items(), key=lambda x: -x[1]["$"])[:5]:
            msg += f"    – {m}: {d['u']}u ${d['$']:,.0f}\n"
        msg += "\n"
        total_neto += s["neto"]
        total_u += s["u"]
    msg += f"━━━━━━━━━━━━━━━\n*TOTAL NETO: ${total_neto:,.0f}*\nUnidades: {total_u}u"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
    print(f"\nTG enviado.")
