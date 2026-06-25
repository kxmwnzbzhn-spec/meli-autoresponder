import os,requests,json
from datetime import datetime,timedelta,timezone
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
SID=3419500448

# 1) All items by status
items=[]
for s in ("active","paused","under_review","closed"):
  off=0
  while True:
    rr=requests.get(f"{API}/users/{SID}/items/search?status={s}&offset={off}&limit=50",headers=H,timeout=15).json()
    res=rr.get("results",[])
    if not res: break
    for iid in res: items.append({"iid":iid,"status":s})
    if len(res)<50: break
    off+=50
print(f"TOTAL ITEMS: {len(items)}")

# Enrich each: price, qty, visits
iids=[i["iid"] for i in items]
all_data={}
# bulk visits
for ch in range(0,len(iids),50):
  vv=requests.get(f"{API}/visits/items?ids={','.join(iids[ch:ch+50])}",headers=H,timeout=15)
  if vv.status_code==200:
    for k,v in vv.json().items(): all_data.setdefault(k,{})["visits"]=v

for iid in iids:
  try:
    it=requests.get(f"{API}/items/{iid}?attributes=id,title,price,available_quantity,sold_quantity,status,sub_status,catalog_listing",headers=H,timeout=8).json()
    all_data.setdefault(iid,{}).update({k:it.get(k) for k in ("title","price","available_quantity","sold_quantity","status","sub_status","catalog_listing")})
  except: pass

# 2) Orders/Sales last 30 days
orders=[]
off=0
date_from=(datetime.now(timezone.utc)-timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000-00:00")
while True:
  rr=requests.get(f"{API}/orders/search?seller={SID}&order.date_created.from={date_from}&offset={off}&limit=50",headers=H,timeout=15).json()
  if "results" not in rr: print("err orders:",rr.get("message","")[:120]); break
  for o in rr["results"]:
    orders.append({
      "id":o["id"],"status":o.get("status"),"status_detail":o.get("status_detail"),
      "total":o.get("total_amount"),"buyer":o.get("buyer",{}).get("nickname"),
      "date":o.get("date_created","")[:10],
      "items":[(i.get("item",{}).get("id"),i.get("item",{}).get("title","")[:50],i.get("quantity")) for i in o.get("order_items",[])]
    })
  if len(rr["results"])<50: break
  off+=50

print(f"\nORDERS last 30d: {len(orders)}")

# Print items summary
print("\n=== ITEMS ===")
print(f"{'iid':17} {'status':12} {'cat':4} {'qty':4} {'sold':5} {'visits':7} {'price':9} title")
sold_total=0; revenue_total=0
for iid in iids:
  d=all_data.get(iid,{})
  sold=(d.get("sold_quantity") or 0)
  sold_total+=sold
  price=d.get("price") or 0
  revenue_total+=sold*price
  cat="Si" if d.get("catalog_listing") else "No"
  print(f" {iid:16} {d.get('status') or '-':11} {cat:3}  {d.get('available_quantity') or 0:>3} {sold:>4} {d.get('visits') or 0:>6}  ${price:>6}  {d.get('title','')[:50]}")

# Print orders
print(f"\n=== ORDERS LAST 30 DAYS ===")
print(f"Total orders: {len(orders)}  total revenue (paid): ${sum(o['total'] or 0 for o in orders if o['status']=='paid')}")
for o in orders[:50]:
  items_str=" + ".join(f"{q}x{t}" for _,t,q in o['items'])
  print(f"  {o['date']} {o['id']} {o['status']:12} ${o['total']:>5} {o['buyer'][:15]:15} {items_str[:80]}")
