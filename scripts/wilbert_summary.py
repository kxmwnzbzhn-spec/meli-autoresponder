import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname")
print(f"=== ACCOUNT: {nick} ({uid}) ===")

# Pull TODAS las orders paid (acumulado histórico)
all_orders=[]
offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&sort=date_desc&limit=50&offset={offset}",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    all_orders.extend(res)
    if len(res)<50: break
    offset+=50
    if offset>1000: break  # safety

# Cancelled
cancelled=[]
offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=cancelled&sort=date_desc&limit=50&offset={offset}",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    cancelled.extend(res)
    if len(res)<50: break
    offset+=50
    if offset>500: break

print(f"Total paid orders: {len(all_orders)}")
print(f"Total cancelled orders: {len(cancelled)}")

# Compute bruto / fees / shipping
gross=0.0; fees=0.0; ship=0.0; qty=0
detail=[]
oldest=None; newest=None
for o in all_orders:
    dt=o.get("date_created","")
    if not oldest or dt<oldest: oldest=dt
    if not newest or dt>newest: newest=dt
    items=o.get("order_items",[])
    for it in items:
        q=it.get("quantity",0) or 0
        up=it.get("unit_price",0) or 0
        sf=it.get("sale_fee",0) or 0
        gross+= up*q
        fees+= sf*q
        qty+=q
    sc=(o.get("shipping",{}) or {}).get("cost") or 0
    # In paid orders, seller pays via list; we'll approximate with payments
    pays=o.get("payments",[])
    ship_cost=0
    for p in pays:
        ship_cost += p.get("shipping_cost",0) or 0
    ship+= ship_cost

net = gross - fees - ship

print(f"\nRango fechas: {oldest} → {newest}")
print(f"Bruto:       ${gross:,.2f}")
print(f"Comision:   -${fees:,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"Envios:     -${ship:,.2f}")
print(f"NETO:        ${net:,.2f}")
print(f"Unidades:    {qty}")
print(f"Ordenes:     {len(all_orders)}")

# Last 10 orders
print("\n--- Últimas 10 órdenes paid ---")
for o in all_orders[:10]:
    items=o.get("order_items",[])
    title=items[0].get("item",{}).get("title","")[:50] if items else ""
    tot=o.get("total_amount",0)
    print(f"  {o.get('date_created','')[:10]} ${tot:>8,.0f}  {title}")

# Cancelaciones por motivo
print("\n--- Cancelaciones (top motivos) ---")
mot={}
for o in cancelled:
    cd=o.get("cancel_detail") or {}
    m=cd.get("description") or cd.get("code") or "?"
    mot[m]=mot.get(m,0)+1
for k,v in sorted(mot.items(),key=lambda x:-x[1])[:8]:
    print(f"  {v}x  {k}")
