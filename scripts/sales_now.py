#!/usr/bin/env python3
"""Ventas MELI HOY (CDMX) por cuenta + total + neto estimado."""
import os, requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID = os.environ.get("TELEGRAM_CHAT_ID","")

ACCS = {
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
}

TZ = timezone(timedelta(hours=-6))
TODAY = datetime.now(TZ).date()
START = datetime(TODAY.year, TODAY.month, TODAY.day, 0,0,0, tzinfo=TZ)
END = START + timedelta(days=1)
print(f"Día: {TODAY} CDMX")

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

summary = {}
for acc, rt in ACCS.items():
    if not rt: continue
    at = tok(rt)
    if not at: continue
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me.get("id")
    if not uid: continue

    orders = []
    offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search",
            headers=H, timeout=20,
            params={"seller":uid,
                    "order.date_created.from":START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":offset}).json()
        res = r.get("results",[])
        if not res: break
        orders.extend(res)
        offset += len(res)
        if offset >= r.get("paging",{}).get("total",0): break

    paid = [o for o in orders if o.get("status")=="paid"]
    canc = [o for o in orders if o.get("status")=="cancelled"]

    bruto = comision = units = 0
    by_model = defaultdict(lambda: {"u":0,"$":0.0})
    for o in paid:
        for it in o.get("order_items",[]):
            qty = it.get("quantity",1)
            up = float(it.get("unit_price",0) or 0)
            sf = float(it.get("sale_fee",0) or 0)
            line = up*qty
            bruto += line
            comision += sf*qty
            units += qty
            t = (it.get("item",{}).get("title","") or "").lower()
            if "go 4" in t or "go4" in t: m="Go 4"
            elif "go 3" in t or "go3" in t: m="Go 3"
            elif "clip 5" in t or "clip5" in t: m="Clip 5"
            elif "charge" in t: m="Charge 6"
            elif "flip" in t: m="Flip 7"
            elif "grip" in t: m="Grip"
            elif "perfum" in t or "edp" in t or "edt" in t: m="Perfumes"
            else: m="Otros"
            by_model[m]["u"]+=qty
            by_model[m]["$"]+=line

    neto = bruto - comision
    summary[acc] = {"orders":len(paid),"canc":len(canc),"u":units,"bruto":bruto,
                    "comision":comision,"neto":neto,"models":dict(by_model)}

# Print
total_u = total_neto = total_bruto = 0
print(f"\n=== Ventas {TODAY} CDMX ===")
for acc, s in sorted(summary.items(), key=lambda x: -x[1]["neto"]):
    if s["orders"] == 0 and s["canc"] == 0: continue
    print(f"\n{acc}: {s['orders']} órdenes / {s['u']}u / bruto ${s['bruto']:,.0f} → neto ${s['neto']:,.0f}")
    if s["canc"]: print(f"  canc: {s['canc']}")
    for m, d in sorted(s["models"].items(), key=lambda x: -x[1]["$"])[:5]:
        print(f"  {m}: {d['u']}u ${d['$']:,.0f}")
    total_u += s["u"]; total_neto += s["neto"]; total_bruto += s["bruto"]

print(f"\n{'='*50}\nTOTAL: {total_u}u / bruto ${total_bruto:,.0f} → neto ${total_neto:,.0f}")

# TG
if TG and TGCID:
    msg = f"💰 *Ventas hoy {TODAY}*\n\n"
    for acc, s in sorted(summary.items(), key=lambda x: -x[1]["neto"]):
        if s["orders"] == 0: continue
        msg += f"*{acc}*: {s['orders']} ord / {s['u']}u\n"
        msg += f"  bruto ${s['bruto']:,.0f} → *neto ${s['neto']:,.0f}*\n"
    msg += f"\n━━━━━━━━━━━\n*TOTAL: {total_u}u | NETO ${total_neto:,.0f}*"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
