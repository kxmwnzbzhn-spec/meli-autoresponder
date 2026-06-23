import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ORDERS=["2000013543063645","2000013543121015"]

for ORDER in ORDERS:
  print(f"\n========== ORDER {ORDER} ==========")
  o=requests.get(f"{API}/orders/{ORDER}",headers=H,timeout=15)
  print(f"GET order: {o.status_code}")
  if o.status_code!=200:
    print(f"  {o.text[:500]}")
    continue
  oj=o.json()
  print(f"  total: ${oj.get('total_amount')}  status: {oj.get('status')}")
  print(f"  buyer: {oj.get('buyer',{}).get('nickname')} (id {oj.get('buyer',{}).get('id')})")
  sid=oj.get("shipping",{}).get("id")
  print(f"  shipping_id: {sid}")
  for it in oj.get("order_items",[]):
    print(f"  item: {it.get('item',{}).get('title','')[:60]} x{it.get('quantity')}")
  
  # Shipment
  if sid:
    s=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=15).json()
    print(f"\n  shipment status: {s.get('status')} sub: {s.get('substatus')}")
    print(f"  tracking: {s.get('tracking_number')}")
    print(f"  date_delivered: {s.get('status_history',{}).get('date_delivered')}")
  
  # Search any claim for this order
  cs=requests.get(f"{API}/post-purchase/v1/claims/search?resource=order&resource_id={ORDER}",headers=H,timeout=15)
  if cs.status_code==200:
    data=cs.json()
    cl=data.get("data") or data.get("results") or []
    print(f"\n  existing claims: {len(cl)}")
    for c in cl:
      print(f"    {c.get('id')} stage={c.get('stage')} reason={c.get('reason_id')}")
  
  # Try probing the seller actions for creating a claim
  # /post-purchase/v1/claims/categories or similar
  print("\n  === probing seller claim creation endpoints ===")
  # Try discover what reasons are available for seller
  rg=requests.get(f"{API}/post-purchase/v1/orders/{ORDER}/claims/configurations",headers=H,timeout=15)
  print(f"  GET /orders/{ORDER}/claims/configurations: {rg.status_code} {rg.text[:400]}")
  
  rg2=requests.get(f"{API}/post-purchase/v1/claims/reasons?role=respondent",headers=H,timeout=15)
  print(f"  GET reasons (seller): {rg2.status_code}")
  if rg2.status_code==200:
    for x in (rg2.json()[:5] if isinstance(rg2.json(),list) else []):
      print(f"    {x}")
  
  # Try /shipments/{id}/seller-claims or /shipment-claims
  for ep in [f"/shipments/{sid}/claims", f"/shipments/{sid}/seller-claims", f"/shipments/{sid}/incidents", f"/shipping/{sid}/claims"]:
    if sid:
      pr=requests.get(f"{API}{ep}",headers=H,timeout=10)
      if pr.status_code<400:
        print(f"  ✓ {ep}: {pr.status_code} {pr.text[:300]}")
