import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# === A) REACTIVAR MLM5525982716 ===
print("=== A) MLM5525982716 reactivar ===")
G="MLM5525982716"
g=requests.get(f"{API}/items/{G}",headers=H,timeout=15).json()
print(f"PRE: status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")
if g.get("status")=="paused":
  # Reactivate
  p1=requests.put(f"{API}/items/{G}",headers=HJ,json={"available_quantity":1},timeout=20)
  print(f"  PUT qty=1: {p1.status_code} {p1.text[:300]}")
  p2=requests.put(f"{API}/items/{G}",headers=HJ,json={"status":"active"},timeout=20)
  print(f"  PUT active: {p2.status_code} {p2.text[:300]}")
  g2=requests.get(f"{API}/items/{G}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"  POST: {g2}")

# === B) CLONAR MLM5525381774 ===
print("\n=== B) Clonar MLM5525381774 ===")
SRC="MLM5525381774"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"src title: {src.get('title')}")
print(f"src price: {src.get('price')} qty={src.get('available_quantity')} sold={src.get('sold_quantity')} status={src.get('status')}")

# Reuse pic IDs (same seller)
pic_ids=[p.get("id") for p in src.get("pictures",[]) if p.get("id")]
print(f"src pics: {len(pic_ids)}")

# Get desc
dr=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=15)
desc=dr.json().get("plain_text","") if dr.status_code==200 else ""
print(f"src desc len: {len(desc)}")

# Build attrs
keep={"BRAND","MODEL","LINE","COLOR","MAIN_COLOR","WITH_BLUETOOTH","IS_WATER_RESISTANT","GTIN","ITEM_CONDITION"}
attrs=[]
for a in src.get("attributes",[]):
  if a.get("id") in keep and (a.get("value_name") or a.get("value_id")):
    attrs.append({"id":a["id"],"value_name":a.get("value_name"),"value_id":a.get("value_id")})

payload={
  "title": src.get("title"),
  "category_id": src.get("category_id") or "MLM59800",
  "price": src.get("price") or 399,
  "currency_id":"MXN",
  "available_quantity": min(src.get("available_quantity") or 100, 200),
  "listing_type_id":"gold_special",
  "condition":"used",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":True,"local_pick_up":False},
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
  print(f"\n✅ CLONED {new_id} @ ${d.get('price')} qty={d.get('available_quantity')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
