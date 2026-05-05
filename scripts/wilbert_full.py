import os, requests
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")
print(f"=== {nick} ({uid}) ===")

# Pull con date_from = hace 60 días, SIN filtro de status
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"Rango: desde {date_from}\n")

all_orders=[]
offset=0
while True:
    url=f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc"
    rr=requests.get(url,headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    all_orders.extend(res)
    if len(res)<50: break
    offset+=50
    if offset>5000: break

print(f"Total órdenes (todos status, últimos 60d): {len(all_orders)}")

# Por status
by_st={}
for o in all_orders:
    st=o.get("status","?")
    by_st[st]=by_st.get(st,0)+1
print(f"Por status: {by_st}\n")

# Acumular SOLO paid+shipped+delivered como ventas válidas
gross=fees=qty=0; orders=0
by_day={}
for o in all_orders:
    if o.get("status") not in ("paid","shipped","delivered"): continue
    orders+=1
    day=o.get("date_created","")[:10]
    g_o=f_o=q_o=0
    for it in o.get("order_items",[]):
        q=it.get("quantity",0) or 0
        up=it.get("unit_price",0) or 0
        sf=it.get("sale_fee",0) or 0
        g_o+=up*q; f_o+=sf*q; q_o+=q
    gross+=g_o; fees+=f_o; qty+=q_o
    d=by_day.setdefault(day,{"o":0,"u":0,"g":0,"n":0})
    d["o"]+=1; d["u"]+=q_o; d["g"]+=g_o; d["n"]+=g_o-f_o

net=gross-fees
print(f"VENTAS válidas (paid/shipped/delivered) últimos 60d:")
print(f"  Órdenes: {orders}")
print(f"  Unidades: {qty}")
print(f"  Bruto:  ${gross:,.2f}")
print(f"  Comis: -${fees:,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"  NETO:   ${net:,.2f}\n")

print(f"=== Por día (últimos 14 días con ventas) ===")
days=sorted(by_day.items(),reverse=True)[:14]
for d,v in days:
    print(f"  {d}  ord={v['o']:>3}  un={v['u']:>3}  bruto=${v['g']:>10,.2f}  neto=${v['n']:>10,.2f}")

# Cancelled count
canc=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=cancelled&order.date_created.from={date_from}&limit=1",headers=H,timeout=20).json()
print(f"\nCanceladas últimos 60d: {canc.get('paging',{}).get('total','?')}")
