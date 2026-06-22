import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ORDER_ID="2000013579459581"

# 1) Order
print(f"=== ORDER {ORDER_ID} ===")
o=requests.get(f"{API}/orders/{ORDER_ID}",headers=H,timeout=15).json()
print(f"total: ${o.get('total_amount')}")
print(f"buyer: {o.get('buyer',{}).get('nickname')} ({o.get('buyer',{}).get('id')})")
shipping_id=o.get("shipping",{}).get("id")
print(f"shipping_id: {shipping_id}")
items=o.get("order_items",[])
total_weight=0
for it in items:
  i=it.get("item",{})
  qty=it.get("quantity",1)
  print(f"  {qty}x {i.get('id')} | {i.get('title','')[:60]} | ${it.get('unit_price')}")
  total_weight += qty * 100  # default fallback

# 2) Shipping/shipment + weight
if shipping_id:
  print(f"\n=== SHIPMENT {shipping_id} ===")
  s=requests.get(f"{API}/shipments/{shipping_id}",headers=H,timeout=15).json()
  print(f"status: {s.get('status')}  substatus: {s.get('substatus')}")
  print(f"tracking: {s.get('tracking_number')}")
  weight_info={}
  sdims=s.get("shipping_option",{}).get("estimated_handling_time")
  if "dimensions" in s.get("shipping_option",{}):
    print(f"dimensions: {s['shipping_option']['dimensions']}")
  # Status history
  sh=s.get("status_history",{})
  print(f"date_delivered: {sh.get('date_delivered')}")
  print(f"date_shipped: {sh.get('date_shipped')}")
  # Find pkg weight
  for k in ("package_weight","weight","total_weight"):
    if s.get(k): print(f"{k}: {s.get(k)}")
  # cost details (peso facturado)
  cost=s.get("cost_components",{}) or s.get("cost",{})
  print(f"cost: {cost}")
  # Get items shipment info for weight
  si=requests.get(f"{API}/shipments/{shipping_id}/items",headers=H,timeout=15)
  print(f"\nshipment items: {si.status_code}")
  if si.status_code==200:
    for x in si.json():
      print(f"  {x}")

# 3) Find claims for this order
print(f"\n=== CLAIMS for order ===")
cs=requests.get(f"{API}/post-purchase/v1/claims/search?resource=order&resource_id={ORDER_ID}",headers=H,timeout=15)
print(f"claims search: {cs.status_code}")
print(cs.text[:1500])
if cs.status_code==200:
  data=cs.json()
  claims=data.get("data") or data.get("results") or []
  print(f"\n→ found {len(claims)} claims")
  for c in claims:
    cid=c.get("id")
    print(f"\n--- CLAIM {cid} ---")
    cf=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15).json()
    print(f"  stage: {cf.get('stage')}  status: {cf.get('status')}")
    print(f"  reason_id: {cf.get('reason_id')}")
    for p in cf.get("players",[]):
      if p.get("role")=="respondent":
        print(f"  seller actions: {[a.get('action') if isinstance(a,dict) else a for a in (p.get('available_actions') or [])]}")
