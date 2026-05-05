"""Cierre Raymundo semana lunes 27 abr - domingo 3 may 2026.
Tira por Telegram el bruto, comision, envios y NETO + breakdown por modelo.
"""
import os, requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

TZ=timezone(timedelta(hours=-6))
# Semana fija: lunes 27 abr 00:00 → lunes 4 may 00:00 (CDMX)
START=datetime(2026,4,27,0,0,0,tzinfo=TZ)
END  =datetime(2026,5,4,0,0,0,tzinfo=TZ)
print(f"Semana Raymundo: {START.date()} → {(END-timedelta(days=1)).date()} CDMX")

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
print(f"Cuenta: {me['nickname']} ({uid})\n")

orders=[]; offset=0
while True:
    rr=requests.get("https://api.mercadolibre.com/orders/search",headers=H,
        params={"seller":uid,
                "order.date_created.from":START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":  END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":offset},timeout=20).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res); offset+=len(res)
    if offset>=rr.get("paging",{}).get("total",0): break

paid=[o for o in orders if o.get("status")=="paid"]
canc=[o for o in orders if o.get("status")=="cancelled"]
print(f"orders fetched: {len(orders)}  paid={len(paid)}  canc={len(canc)}")

bruto=0.0; comision=0.0; envios=0.0; units=0
by_model=defaultdict(lambda:{"u":0,"$":0.0})
by_day  =defaultdict(lambda:{"u":0,"neto":0.0})

for o in paid:
    dc=o.get("date_created","")
    try:
        day=datetime.fromisoformat(dc.replace("Z","+00:00")).astimezone(TZ).date().isoformat()
    except: day="?"
    line_total=0.0; fee_total=0.0; q_total=0
    for it in o.get("order_items",[]):
        qty=it.get("quantity",1)
        up=float(it.get("unit_price",0) or 0)
        sf=float(it.get("sale_fee",0) or 0)
        line=up*qty; fee=sf*qty
        bruto+=line; comision+=fee; units+=qty
        line_total+=line; fee_total+=fee; q_total+=qty
        t=(it.get("item",{}).get("title","") or "").lower()
        if   "go 4" in t or "go4" in t: m="Go 4"
        elif "go 3" in t or "go3" in t: m="Go 3"
        elif "clip 5" in t or "clip5" in t: m="Clip 5"
        elif "charge" in t: m="Charge 6"
        elif "flip" in t: m="Flip 7"
        elif "grip" in t: m="Grip"
        elif "bose" in t or "soundlink" in t: m="Bose"
        elif "sony" in t or "xb100" in t: m="Sony"
        else: m="Otros"
        by_model[m]["u"]+=qty
        by_model[m]["$"]+=line
    sh=o.get("shipping",{}) or {}
    cost=float(sh.get("cost") or 0)
    envios+=cost
    by_day[day]["u"]+=q_total
    by_day[day]["neto"]+=(line_total-fee_total-cost)

neto=bruto-comision-envios

print(f"\n=== RESUMEN RAYMUNDO ===")
print(f"orders paid: {len(paid)}  units: {units}  cancelled: {len(canc)}")
print(f"BRUTO    : ${bruto:,.0f}")
print(f"comision : -${comision:,.0f}")
print(f"envios   : -${envios:,.0f}")
print(f"NETO     : ${neto:,.0f}")
print(f"\nPor modelo:")
for m,d in sorted(by_model.items(), key=lambda x:-x[1]['$']):
    print(f"  {m}: {d['u']}u  ${d['$']:,.0f}")
print(f"\nPor día:")
for day in sorted(by_day):
    print(f"  {day}: {by_day[day]['u']}u  NETO ${by_day[day]['neto']:,.0f}")

if TG and TGCID:
    msg=f"💰 *RAYMUNDO — Cierre Semanal*\n"
    msg+=f"_{START.date()} → {(END-timedelta(days=1)).date()}_\n\n"
    msg+=f"*NETO: ${neto:,.0f}*\n"
    msg+=f"Bruto: ${bruto:,.0f}\n"
    msg+=f"Comisión: -${comision:,.0f}\n"
    msg+=f"Envíos:   -${envios:,.0f}\n"
    msg+=f"Unidades: *{units}u* en {len(paid)} órdenes\n"
    if canc: msg+=f"Canceladas: {len(canc)}\n"
    msg+=f"\n*Por modelo:*\n"
    for m,d in sorted(by_model.items(), key=lambda x:-x[1]['$']):
        msg+=f"• {m}: {d['u']}u — ${d['$']:,.0f}\n"
    msg+=f"\n*Por día:*\n"
    for day in sorted(by_day):
        msg+=f"• {day[5:]}: {by_day[day]['u']}u  ${by_day[day]['neto']:,.0f}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]},timeout=20)
    print("\n✅ Telegram enviado")
