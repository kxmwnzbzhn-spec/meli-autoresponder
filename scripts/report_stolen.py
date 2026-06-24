import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

cp=requests.get(f"{API}/products/MLM44731934",headers=HJ,timeout=15).json()
print("CPID:",cp.get("name"))
payload={
  "catalog_listing": True,
  "catalog_product_id": "MLM44731934",
  "category_id": "MLM59800",
  "price": 599,
  "currency_id": "MXN",
  "available_quantity": 1,
  "listing_type_id": "gold_pro",
  "condition": "new",
  "title": "Bocina JBL Go 4 Portátil Bluetooth Waterproof Negra",
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"PUBLISH: {r.status_code}")
print(r.text[:1200])
