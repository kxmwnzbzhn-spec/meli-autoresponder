import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM28067123"
TITLE="Perfume Armaf Club de Nuit Iconic Eau de Parfum 105 mL"  # 55
print(f"title len: {len(TITLE)}")
payload={
  "title": TITLE,
  "catalog_product_id": CPID,
  "catalog_listing": True,
  "category_id":"MLM1271",
  "price":649,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_pro",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ]
}
p=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=payload,timeout=30)
print(f"POST: {p.status_code}")
print(p.text[:2000])
if p.status_code==201:
  d=p.json()
  print(f"\n✅ CATALOG CREATED {d.get('id')} @ ${d.get('price')} status={d.get('status')} CPID={d.get('catalog_product_id')}")
  print(f"permalink: {d.get('permalink')}")
