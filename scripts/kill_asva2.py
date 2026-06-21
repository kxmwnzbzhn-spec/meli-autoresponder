import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for SRC,PRICE,LABEL in [("MLM3849137034",999,"Alma de Tenochtitlán"),("MLM2378087893",999,"Flor de Nopal")]:
  print(f"\n=== Republicando {SRC} ({LABEL}) ===")
  src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
  CAT=src.get("category_id")
  CPID=src.get("catalog_product_id")
  LIST_TYPE=src.get("listing_type_id") or "gold_special"
  print(f"  category: {CAT} | CPID: {CPID} | list_type: {LIST_TYPE}")
  
  # Catalog listing: NO title
  payload={
    "catalog_product_id":CPID,
    "catalog_listing":True,
    "category_id":CAT,
    "price":PRICE,
    "currency_id":"MXN",
    "available_quantity":1,
    "listing_type_id":LIST_TYPE,
    "condition":"new",
    "buying_mode":"buy_it_now",
    "sale_terms":[
      {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
      {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
  }
  p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  print(f"  POST: {p.status_code}")
  if p.status_code==201:
    d=p.json()
    print(f"  ✅ RE-PUBLICADO {d.get('id')} @ ${d.get('price')} status={d.get('status')}")
    print(f"  permalink: {d.get('permalink')}")
  else:
    print(f"  ❌ {p.text[:600]}")
