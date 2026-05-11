import os, requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
print(f"=== {nick} ({uid}) — corte {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===\n")

# Pull TODAS las orders desde inicio (90d cubre)
since=cdmx-timedelta(days=90)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")

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

# Acumular por estatus de envío
def get_ship_info(sid,h):
    try:
        # /shipments/{id} para status + delivered_date
        r1=requests.get(f"https://api.mercadolibre.com/shipments/{sid}",headers=h,timeout=10).json()
        ship_status=r1.get("status","?")
        substatus=r1.get("substatus","")
        date_delivered=None
        for k in ["status_history","tracking_history"]:
            hist=r1.get(k) or []
            if hist:
                for e in hist:
                    if e.get("status")=="delivered":
                        date_delivered=e.get("date") or e.get("date_status")
                        break
        # /shipments/{id}/costs para sender cost
        r2=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10).json()
        s=r2.get("senders",[])
        if isinstance(s,list): cost=float(sum(x.get("cost",0) or 0 for x in s))
        else: cost=float(s.get("cost",0) or 0)
        return ship_status, substatus, date_delivered, cost
    except:
        return "err", "", None, 0.0

gross=fees=qty=0
days_by={}
sids=[]
order_data=[]
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
    sids.append(sid)
    order_data.append({"id":o.get("id"),"day":day,"gross":g_o,"fees":f_o,"sid":sid,
                       "date_created":o.get("date_created","")})
    d=days_by.setdefault(day,{"o":0,"u":0,"g":0,"f":0,"net_bruto":0})
    d["o"]+=1; d["u"]+=q_o; d["g"]+=g_o; d["f"]+=f_o; d["net_bruto"]+= g_o - f_o

# Refunds reales
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

# Ship info paralelo
print(f"Consultando {len(sids)} shipments (status + costos)…")
ship_results={}
def fetch(sid):
    if not sid: return sid, None
    return sid, get_ship_info(sid, H)

with ThreadPoolExecutor(max_workers=15) as ex:
    futs=[ex.submit(fetch, sid) for sid in sids if sid]
    for f in as_completed(futs):
        sid, info = f.result()
        if info: ship_results[sid]=info

ship_total=0.0
# Clasificar orders: released vs garantía
fortnight_ago=cdmx-timedelta(days=14)
ord_released_count=0; ord_garantia_count=0
gross_released=fees_released=ship_released=0
gross_garantia=fees_garantia=ship_garantia=0
status_count={}

for od in order_data:
    sid=od["sid"]
    info=ship_results.get(sid)
    cost=0.0; sh_st="?"; deliv_date=None
    if info:
        sh_st, substat, deliv_date, cost = info
    ship_total+=cost
    status_count[sh_st]=status_count.get(sh_st,0)+1
    
    # Liberado si: entregado >14d, O delivered hace más de 14 días, O paid >21d
    # Heurística simple: order_created >14 days AND ship status="delivered"
    order_created_dt=datetime.fromisoformat(od["date_created"].replace("Z","+00:00")) if od["date_created"] else None
    if order_created_dt:
        days_since=(cdmx.replace(tzinfo=timezone(timedelta(hours=-6))) - order_created_dt.astimezone(timezone(timedelta(hours=-6)))).days
    else:
        days_since=0
    
    released = (sh_st=="delivered" and days_since>=8)  # MELI estándar libera ~8-14 días post-delivered
    
    if released:
        ord_released_count+=1
        gross_released+= od["gross"]; fees_released+= od["fees"]; ship_released+= cost
    else:
        ord_garantia_count+=1
        gross_garantia+= od["gross"]; fees_garantia+= od["fees"]; ship_garantia+= cost

print(f"\nTotal paid orders: {len(paid)}")
print(f"Shipment statuses: {status_count}")
print(f"  Orders RELEASED (delivered + ≥8d): {ord_released_count}")
print(f"  Orders GARANTÍA (aún retenido): {ord_garantia_count}")

neto_released = gross_released - fees_released - ship_released
neto_garantia = gross_garantia - fees_garantia - ship_garantia

print(f"\n=== TOTALES desde inicio (28-abr) ===")
print(f"Bruto total:           ${gross:>13,.2f}")
print(f"Comisión MELI:        -${fees:>13,.2f}")
print(f"Envío seller:         -${ship_total:>13,.2f}")
print(f"Refunds post-release: -${refund:>13,.2f}")
print(f"NETO contable:         ${gross-fees-ship_total-refund:>13,.2f}")

print(f"\n=== SALDO MP DISPONIBLE ESTIMADO ===")
print(f"Liberado (delivered+8d):${neto_released:>11,.2f}")
print(f"En garantía MP (no liberable hoy): ${neto_garantia:>11,.2f}")
print(f"(-) Refunds:                       -${refund:>11,.2f}")
print(f"(-) Retiro 10-may a banco:        -${18300:>11,.2f}")

saldo_estimado_disponible = neto_released - refund - 18300
print(f"= SALDO MP DISPONIBLE HOY:          ${saldo_estimado_disponible:>11,.2f}")

print(f"\n=== VENTAS POR DÍA ===")
for d in sorted(days_by.keys()):
    v=days_by[d]
    days_back=(datetime.now(timezone.utc)-datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc)).days
    rel_marker = "(LIBERADO)" if days_back>14 else f"(en garantía, {14-days_back}d para liberar)"
    print(f"  {d} → órd={v['o']:>3} un={v['u']:>3} bruto=${v['g']:>10,.2f} {rel_marker}")
