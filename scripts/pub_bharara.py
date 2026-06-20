import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM3025553813"
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
print(f"PRE: status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')} price={g.get('price')}")
print(f"title: {g.get('title')}")

# Try to reactivate
p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"active"},timeout=20)
print(f"\nPUT status=active: {p1.status_code} {p1.text[:400]}")
p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":1},timeout=20)
print(f"PUT qty=1: {p2.status_code} {p2.text[:400]}")

g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
print(f"\nPOST: {g2}")

# If still closed, we need to clone
if g2.get("status")!="active":
  print("\n=== CANNOT REACTIVATE — cloning as new listing ===")
  # Get full item
  full=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
  pic_ids=[p.get("id") for p in full.get("pictures",[]) if p.get("id")]
  
  # Get description
  dr=requests.get(f"{API}/items/{IID}/description",headers=H,timeout=15)
  desc=dr.json().get("plain_text","") if dr.status_code==200 else ""
  
  # Build clone
  attrs=[]
  keep_ids={"BRAND","MODEL","LINE","COLOR","MAIN_COLOR","WITH_BLUETOOTH","IS_WATER_RESISTANT","GTIN","ITEM_CONDITION"}
  for a in full.get("attributes",[]):
    if a.get("id") in keep_ids and (a.get("value_name") or a.get("value_id")):
      attrs.append({"id":a["id"],"value_name":a.get("value_name"),"value_id":a.get("value_id")})
  
  payload={
    "title": full.get("title"),
    "category_id": full.get("category_id"),
    "price": full.get("price") or 599,
    "currency_id":"MXN",
    "available_quantity":1,
    "listing_type_id":"gold_special",
    "condition":"used",
    "buying_mode":"buy_it_now",
    "pictures":[{"id":p} for p in pic_ids],
    "attributes": attrs,
    "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
    "sale_terms":[
      {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
      {"id":"WARRANTY_TIME","value_name":"30 días"}
    ],
    "description":{"plain_text":desc[:5000]}
  }
  
  p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  print(f"\nPOST clone: {p.status_code}")
  print(p.text[:1500])
  if p.status_code==201:
    d=p.json()
    new_id=d.get("id")
    pd=requests.post(f"{API}/items/{new_id}/description",headers=HJ,json={"plain_text":desc[:5000]},timeout=20)
    print(f"\n✅ CLONED {new_id} @ ${d.get('price')} status={d.get('status')}")
    print(f"permalink: {d.get('permalink')}")
