import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

cp=requests.get(f"{API}/products/MLM44710240",headers=HJ,timeout=15).json()
fname=cp.get("family_name") or cp.get("name") or "Bocina JBL Go 4 Negra"
print("family_name:",fname)

# Try with family_name
payload={
  "catalog_listing": True,
  "catalog_product_id": "MLM44710240",
  "category_id": "MLM1051",
  "price": 599,
  "currency_id": "MXN",
  "available_quantity": 1,
  "listing_type_id": "gold_pro",
  "condition": "new",
  "family_name": fname,
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\nPUBLISH family_name: {r.status_code}")
print(r.text[:800])
if r.status_code==201:
  print("\n=== SUCCESS ===")
else:
  # Try with title
  payload2=dict(payload); del payload2["family_name"]; payload2["title"]=fname[:60]
  r2=requests.post(f"{API}/items",headers=HJ,json=payload2,timeout=30)
  print(f"\nPUBLISH title: {r2.status_code}")
  print(r2.text[:800])
