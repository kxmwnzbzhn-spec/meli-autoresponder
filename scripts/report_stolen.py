import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

payload={
  "catalog_listing": True,
  "catalog_product_id": "MLM52129273",
  "category_id": "MLM1271",
  "price": 299,
  "currency_id": "MXN",
  "available_quantity": 1,
  "listing_type_id": "gold_pro",
  "condition": "new",
  "sale_terms": [{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print("PUBLISH:",r.status_code)
print(r.text[:1500])
