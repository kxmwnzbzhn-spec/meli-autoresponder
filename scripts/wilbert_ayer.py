import os, requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")

# Ayer en CDMX: 12-may 00:00 a 12-may 23:59 CDMX
cdmx_yest_start = datetime(2026,5,12,0,0,0,tzinfo=timezone(timedelta(hours=-6)))
cdmx_yest_end   = datetime(2026,5,12,23,59,59,tzinfo=timezone(timedelta(hours=-6)))
date_from = cdmx_yest_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
date_to   = cdmx_yest_end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

print(f"=== {nick} — CIERRE AYER 12/05/2026 (00:00-23:59 CDMX) ===\n")

# Pull todas las orders del día
orders=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res)
    if len(res)<50: break
    offset+=50

paid=[o for o in orders if o.get("status") in ("paid","shipped","delivered")]
cancelled=[o for o in orders if o.get("status")=="cancelled"]

gross=fees=qty=0; sids=[]
items_count={}
for o in paid:
    for it in o.get("order_items",[]):
        q=it.get("quantity",0) or 0
        gross+=(it.get("unit_price",0) or 0)*q
        fees+=(it.get("sale_fee",0) or 0)*q
        qty+=q
        title=it.get("item",{}).get("title","")[:55]
        if title:
            e=items_count.setdefault(title,{"u":0,"r":0})
            e["u"]+=q; e["r"]+=up*q if False else (it.get("unit_price",0) or 0)*q
    sid=(o.get("shipping",{}) or {}).get("id")
    if sid: sids.append(sid)

# Refunds intra-día
refund=0
for o in cancelled:
    for p in (o.get("payments") or []):
        if p.get("status")=="refunded":
            refund += p.get("transaction_amount_refunded",0) or 0

def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

ship=0.0
if sids:
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(get_ship,sid,H) for sid in sids]
        for f in as_completed(futs):
            ship+=f.result()

retencion = gross * 0.0228
neto_mp = gross - fees - ship - refund - retencion
iva = gross * 0.16 / 1.16
neto_real = neto_mp - iva

print(f"Órdenes paid:  {len(paid)}")
print(f"Canceladas:    {len(cancelled)}")
print(f"Unidades:      {qty}")
print(f"\nDESGLOSE:")
print(f"  Bruto:           ${gross:>13,.2f}")
print(f"  Comis MELI:     -${fees:>13,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"  Envío seller:   -${ship:>13,.2f}  (avg ${ship/len(sids) if sids else 0:.2f}/ord)")
print(f"  Refund intra-día:-${refund:>13,.2f}")
print(f"  Retención 2.28%:-${retencion:>13,.2f}")
print(f"  ─────────────────────────────────")
print(f"  NETO MP (entra al saldo): ${neto_mp:>13,.2f}")
print(f"  ─────────────────────────────────")
print(f"  IVA 16%:        -${iva:>13,.2f}")
print(f"  NETO REAL:       ${neto_real:>13,.2f}")
print(f"\nMargen NETO MP / Bruto: {neto_mp/gross*100 if gross else 0:.1f}%")
print(f"Margen NETO real / Bruto: {neto_real/gross*100 if gross else 0:.1f}%")

print(f"\nTOP MODELOS:")
for t,e in sorted(items_count.items(),key=lambda x:-x[1]["r"])[:10]:
    print(f"  {e['u']:>3}u  ${e['r']:>9,.0f}  {t}")
