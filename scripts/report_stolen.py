import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Get Mayrely user info
me=requests.get(f"{API}/users/me",headers=HJ,timeout=15).json()
print("MAYRELY user_id:",me.get("id"),"nickname:",me.get("nickname"))

# Inspect CPID
cp=requests.get(f"{API}/products/MLM44710240",headers=HJ,timeout=15).json()
print("CPID:",cp.get("name"))
print("domain:",cp.get("domain_id"))
# Find category
cat="MLM1051"  # Bocinas Bluetooth
for a in (cp.get("attributes") or []):
  if a.get("id")=="CATEGORY": cat=a.get("value_id") or cat

# Publish payload
payload={
  "catalog_listing": True,
  "catalog_product_id": "MLM44710240",
  "category_id": "MLM1051",
  "price": 599,
  "currency_id": "MXN",
  "available_quantity": 1,
  "listing_type_id": "gold_pro",
  "condition": "new",
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\nPUBLISH: {r.status_code}")
print(r.text[:1500])
