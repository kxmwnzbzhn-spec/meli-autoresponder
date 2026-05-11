import os, requests, time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
print(f"=== {nick} ({uid}) — corte {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===\n")

since=cdmx-timedelta(days=90)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Pull orders
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
print(f"Total: paid={len(paid)} cancelled={len(cancelled)}\n")

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
    sid=(o.get("shipping",{}) or {}).get("id")
    if sid: sids.append(sid)
    d=by_day.setdefault(day,{"o":0,"u":0,"g":0,"f":0})
    d["o"]+=1; d["u"]+=q_o; d["g"]+=g_o; d["f"]+=f_o

# Refunds post-release
def is_post(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

refund=0
for o in cancelled:
    if not is_post(o): continue
    for p in (o.get("payments") or []):
        if p.get("status")=="refunded":
            refund+=p.get("transaction_amount_refunded",0) or 0

# Ship costs con retries y menos paralelismo
def get_ship_cost(sid, retries=2):
    for _ in range(retries+1):
        try:
            r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=H,timeout=20)
            if r.status_code==200:
                j=r.json(); s=j.get("senders",[])
                if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
                return float(s.get("cost",0) or 0)
        except: 
            time.sleep(0.3)
    return None

ship_total=0; ok=0; err=0
print(f"Consultando {len(sids)} shipments con retries (max workers=8)…")
with ThreadPoolExecutor(max_workers=8) as ex:
    futs={ex.submit(get_ship_cost, sid): sid for sid in sids}
    for f in as_completed(futs):
        c=f.result()
        if c is not None: ship_total+=c; ok+=1
        else: err+=1

print(f"OK: {ok}, ERR: {err}")
if err > 0:
    # Estimar para los que fallaron
    avg=ship_total/ok if ok else 70
    ship_total += avg*err
    print(f"Estimado ${avg:.2f}/ord para los {err} faltantes → total $-{ship_total:,.2f}")

# IVA
iva = (gross - refund) * 0.16 / 1.16 if (gross-refund)>0 else 0
neto_contable = gross - fees - ship_total - refund
neto_real = neto_contable - iva

print(f"\n=== DESGLOSE COMPLETO (desde 28-abr) ===")
print(f"Bruto:           ${gross:>13,.2f}")
print(f"Comis MELI:     -${fees:>13,.2f}  ({fees/gross*100:.1f}%)")
print(f"Envío seller:   -${ship_total:>13,.2f}  (avg ${ship_total/len(sids):.2f}/orden)")
print(f"Refunds post:   -${refund:>13,.2f}")
print(f"NETO contable:   ${neto_contable:>13,.2f}")
print(f"IVA 16%:        -${iva:>13,.2f}")
print(f"NETO REAL:       ${neto_real:>13,.2f}  ← total ganado en libros")
print(f"(-) Retiro 10-may:-${18300:>13,.2f}")
print(f"= NETO disponible: ${neto_real - 18300:>11,.2f}")

print(f"\n=== POR DÍA ===")
for d in sorted(by_day.keys()):
    v=by_day[d]
    days_back=(cdmx.date()-datetime.strptime(d,"%Y-%m-%d").date()).days
    rel="(liberado)" if days_back>14 else f"(garantía, faltan {14-days_back}d)"
    print(f"  {d}  órd={v['o']:>4}  un={v['u']:>4}  bruto=${v['g']:>11,.2f}  comis=${v['f']:>9,.2f}  {rel}")
