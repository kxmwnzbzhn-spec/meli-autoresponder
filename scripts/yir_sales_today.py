import os, requests, datetime as dt
from datetime import timezone, timedelta
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

TZ_M=timezone(timedelta(hours=-6))
today=dt.datetime.now(TZ_M).date()
start=dt.datetime.combine(today, dt.time.min, TZ_M)
end=dt.datetime.combine(today, dt.time.max, TZ_M)
sf=start.strftime("%Y-%m-%dT%H:%M:%S.000-06:00")
ef=end.strftime("%Y-%m-%dT%H:%M:%S.999-06:00")

print(f"Yiriam uid={uid}  fecha CDMX: {today}")
print(f"Rango: {sf} → {ef}\n")

total_qty=0
total_amt=0
n_orders=0
offset=0
detail=[]
while True:
    r=requests.get(f"{API}/orders/search",headers=H,timeout=15,params={
        "seller":uid,
        "order.date_created.from":sf,
        "order.date_created.to":ef,
        "limit":50,"offset":offset
    }).json()
    res=r.get("results") or []
    if not res: break
    for o in res:
        n_orders+=1
        st=o.get("status")
        if st in ("cancelled",): continue
        amt=o.get("total_amount") or 0
        total_amt += amt
        for it in (o.get("order_items") or []):
            qty=it.get("quantity",0)
            iid=(it.get("item") or {}).get("id")
            title=(it.get("item") or {}).get("title","")[:35]
            total_qty += qty
            detail.append((o.get("date_created","")[11:19], iid, qty, it.get("unit_price"), title, st))
    if len(res)<50: break
    offset+=50
    if offset>500: break

print(f"Pedidos hoy: {n_orders}")
print(f"Piezas vendidas: {total_qty}")
print(f"Total $: {total_amt:,.0f}")
print()
print("Detalle (hora CDMX, item, qty, precio, título, status):")
for d in detail:
    print(f"  {d[0]}  {d[1]:<14}  qty={d[2]}  ${d[3]}  '{d[4]}'  [{d[5]}]")
