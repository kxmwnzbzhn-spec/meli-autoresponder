import os, requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")
created_str=me.get("registration_date","") or "?"
print(f"=== {nick} ({uid}) ===")
print(f"Cuenta creada: {created_str}")

# Pull 90 días — cubre toda la historia de Wilbert (creada 28-abr-2026)
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=90)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"Periodo: desde {since.strftime('%Y-%m-%d')} hasta hoy {cdmx.strftime('%Y-%m-%d %H:%M')} CDMX\n")

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
print(f"Total: {len(orders)}  paid={len(paid)}  cancelled={len(cancelled)}")

gross=fees=qty=0; sids=[]
by_day={}
for o in paid:
    day=o.get("date_created","")[:10]
    g_o=f_o=q_o=0
    for it in o.get("order_items",[]):
        q=it.get("quantity",0) or 0
        g_o+=(it.get("unit_price",0) or 0)*q
        f_o+=(it.get("sale_fee",0) or 0)*q
        q_o+=q
    gross+=g_o; fees+=f_o; qty+=q_o
    d=by_day.setdefault(day,{"o":0,"u":0,"g":0,"n":0,"c":0,"s":0})
    d["o"]+=1; d["u"]+=q_o; d["g"]+=g_o
    sid=(o.get("shipping",{}) or {}).get("id")
    if sid: sids.append(sid)

def is_post(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

refund_post=0
for o in cancelled:
    if not is_post(o): continue
    for p in (o.get("payments") or []):
        if p.get("status")=="refunded":
            refund_post += p.get("transaction_amount_refunded",0) or 0

def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

ship=0.0
print(f"Consultando {len(sids)} shipments…")
if sids:
    with ThreadPoolExecutor(max_workers=15) as ex:
        futs=[ex.submit(get_ship,sid,H) for sid in sids]
        for f in as_completed(futs):
            ship+=f.result()

iva = (gross-refund_post) * 0.16 / 1.16 if (gross-refund_post)>0 else 0
neto_mp = gross - fees - ship - refund_post
neto_real = neto_mp - iva

first_day=min(by_day.keys()) if by_day else "?"
last_day=max(by_day.keys()) if by_day else "?"

print(f"\n=== TOTAL DESDE INICIO (cuenta creada 28-abr-2026) ===")
print(f"Rango ventas: {first_day} → {last_day}")
print(f"Días con ventas: {len(by_day)}")
print(f"\nÓrdenes paid:    {len(paid)}")
print(f"Canceladas:      {len(cancelled)}")
print(f"Unidades:        {qty}")
print(f"\nDESGLOSE COMPLETO:")
print(f"  Bruto:           ${gross:>13,.2f}")
print(f"  Comis MELI:     -${fees:>13,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"  Envío seller:   -${ship:>13,.2f}  (avg ${ship/len(sids) if sids else 0:.2f}/orden)")
print(f"  Refund post-rel:-${refund_post:>13,.2f}")
print(f"  ─────────────────────────────────")
print(f"  NETO MP:         ${neto_mp:>13,.2f}")
print(f"  IVA 16%:        -${iva:>13,.2f}")
print(f"  ─────────────────────────────────")
print(f"  NETO REAL:       ${neto_real:>13,.2f}  ← lo que ganamos en libros desde que abrimos la cuenta")

print(f"\nMargen NETO Real / Bruto: {neto_real/gross*100 if gross else 0:.1f}%")
print(f"Promedio diario: ${neto_real/len(by_day) if by_day else 0:,.2f}/día")
print(f"Promedio por orden: ${neto_real/len(paid) if paid else 0:,.2f}/orden")
