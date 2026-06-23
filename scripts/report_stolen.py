import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for PACK in ["2000013543063645","2000013543121015"]:
  print(f"\n========== PACK {PACK} ==========")
  p=requests.get(f"{API}/packs/{PACK}",headers=H,timeout=15).json()
  print(json.dumps(p,ensure_ascii=False,indent=2)[:2000])
  
  # extract order_id from pack
  orders=p.get("orders",[]) or []
  for o in orders:
    oid=o.get("id")
    print(f"\n  --- ORDER {oid} ---")
    ordr=requests.get(f"{API}/orders/{oid}",headers=H,timeout=15).json()
    print(f"    total: ${ordr.get('total_amount')}  buyer: {ordr.get('buyer',{}).get('nickname')}")
    sid=ordr.get("shipping",{}).get("id")
    print(f"    shipping_id: {sid}")
    for it in ordr.get("order_items",[]):
      print(f"    item: {it.get('item',{}).get('title','')[:60]} ${it.get('unit_price')}")
    
    if sid:
      s=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=15).json()
      print(f"    shipment status: {s.get('status')} sub: {s.get('substatus')}")
      print(f"    tracking: {s.get('tracking_number')}")
      print(f"    date_delivered: {s.get('status_history',{}).get('date_delivered')}")
    
    # Check existing claims
    cs=requests.get(f"{API}/post-purchase/v1/claims/search?resource=order&resource_id={oid}",headers=H,timeout=15)
    if cs.status_code==200:
      data=cs.json()
      cl=data.get("data") or data.get("results") or []
      print(f"    existing claims: {len(cl)}")
      for c in cl:
        print(f"      claim {c.get('id')} stage={c.get('stage')} status={c.get('status')} reason={c.get('reason_id')}")
