import os, requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
midnight_cdmx=cdmx.replace(hour=0,minute=0,second=0,microsecond=0)
midnight_utc=midnight_cdmx+timedelta(hours=6)
date_from=midnight_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== {nick} ({uid}) — VENTAS HOY {cdmx.strftime('%d/%m/%Y')} ({cdmx.strftime('%H:%M')} CDMX) ===\n")

orders=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res)
    if len(res)<50: break
    offset+=50

paid=[o for o in orders if o.get("status") in ("paid","shipped","delivered")]
cancelled=[o for o in orders if o.get("status")=="cancelled"]

gross=fees=qty=0
sids=[]
items_count={}
for o in paid:
    for it in o.get("order_items",[]):
        q=it.get("quantity",0) or 0
        up=it.get("unit_price",0) or 0
        sf=it.get("sale_fee",0) or 0
        gross+=up*q; fees+=sf*q; qty+=q
        title=it.get("item",{}).get("title","")[:55]
        if title:
            e=items_count.setdefault(title,{"u":0,"r":0})
            e["u"]+=q; e["r"]+=up*q
    sid=(o.get("shipping",{}) or {}).get("id")
    if sid: sids.append(sid)

# Refunds post-release de cancelaciones de hoy
def is_post(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

refund_post=0
for o in cancelled:
    for p in (o.get("payments") or []):
        if p.get("status")=="refunded" and is_post(o):
            refund_post += p.get("transaction_amount_refunded",0) or 0

# Shipping costs reales por shipment (paralelo)
def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

ship_total=0.0
print(f"Consultando {len(sids)} shipments…")
if sids:
    with ThreadPoolExecutor(max_workers=15) as ex:
        futs=[ex.submit(get_ship,sid,H) for sid in sids]
        for f in as_completed(futs):
            ship_total+=f.result()

# IVA: precios MELI MX incluyen IVA 16%
iva = gross * 0.16 / 1.16

# NETO MP (lo que entra al saldo MP de Wilbert):
neto_mp = gross - fees - ship_total - refund_post

# NETO contable después de IVA (lo que se queda fiscal/utilidad bruta):
neto_after_iva = neto_mp - iva

print(f"\nÓrdenes paid: {len(paid)}  | Canceladas: {len(cancelled)}  | Unidades: {qty}")
print(f"\nDESGLOSE:")
print(f"  Bruto:           ${gross:>13,.2f}")
print(f"  Comis MELI:     -${fees:>13,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"  Envío seller:   -${ship_total:>13,.2f}  (avg ${ship_total/len(sids) if sids else 0:.2f}/orden)")
print(f"  Refund post-rel:-${refund_post:>13,.2f}")
print(f"  ─────────────────────────────────")
print(f"  NETO MP:         ${neto_mp:>13,.2f}  (entra al saldo MP)")
print(f"  ─────────────────────────────────")
print(f"  IVA 16% (sobre bruto/1.16): -${iva:>13,.2f}")
print(f"  NETO REAL después IVA:       ${neto_after_iva:>13,.2f}  (utilidad bruta antes de costo del producto)")
print(f"\nMargen NETO MP / Bruto: {neto_mp/gross*100 if gross else 0:.1f}%")
print(f"Margen NETO real / Bruto: {neto_after_iva/gross*100 if gross else 0:.1f}%")
