import os, requests
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
midnight_cdmx=cdmx.replace(hour=0,minute=0,second=0,microsecond=0)
midnight_utc=midnight_cdmx+timedelta(hours=6)
date_from=midnight_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== {nick} ({uid}) — VENTAS HOY {cdmx.strftime('%d/%m/%Y')} ({cdmx.strftime('%H:%M')} CDMX) ===")
print(f"Desde {date_from}\n")

orders=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res)
    if len(res)<50: break
    offset+=50

paid=cancelled=0; gross=fees=qty=0
items_count={}
for o in orders:
    st=o.get("status","")
    if st=="cancelled": cancelled+=1; continue
    if st in ("paid","shipped","delivered"):
        paid+=1
        for it in o.get("order_items",[]):
            q=it.get("quantity",0) or 0
            up=it.get("unit_price",0) or 0
            sf=it.get("sale_fee",0) or 0
            gross+=up*q; fees+=sf*q; qty+=q
            t=it.get("item",{}).get("title","")[:60]
            e=items_count.setdefault(t,{"u":0,"r":0})
            e["u"]+=q; e["r"]+=up*q

net=gross-fees
print(f"Órdenes paid: {paid}")
print(f"Canceladas:   {cancelled}")
print(f"Unidades:     {qty}")
print(f"Bruto:  ${gross:,.2f}")
print(f"Comis: -${fees:,.2f}")
print(f"NETO:   ${net:,.2f}\n")

print("=== Productos vendidos hoy ===")
for t,e in sorted(items_count.items(),key=lambda x:-x[1]["r"]):
    print(f"  {e['u']:>3}u  ${e['r']:>10,.0f}  {t}")
