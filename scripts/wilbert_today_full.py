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
print(f"=== {nick} ({uid}) — TODO HOY {cdmx.strftime('%d/%m/%Y %H:%M')} CDMX ===")
print(f"date_from={date_from}\n")

# Pull TODAS las órdenes (sin filtrar status)
orders=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res)
    if len(res)<50: break
    offset+=50

print(f"Total órdenes hoy (todas status): {len(orders)}\n")
by_st={}
for o in orders:
    st=o.get("status","?")
    by_st[st]=by_st.get(st,0)+1
print("Por status:")
for k,v in sorted(by_st.items(),key=lambda x:-x[1]):
    print(f"  {k:<20} {v}")

# También revisar /sales y /shipments por si hay otra vista
print("\n--- Items vendidos hoy (cualquier estado) ---")
for o in orders:
    st=o.get("status","")
    items=o.get("order_items",[])
    title=items[0].get("item",{}).get("title","")[:55] if items else ""
    qty=sum(it.get("quantity",0) for it in items)
    amt=o.get("total_amount",0)
    print(f"  {o.get('date_created','')[:19]:<19} {st:<20} q={qty} ${amt:>7,.0f}  {title}")
