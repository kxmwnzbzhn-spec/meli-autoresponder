import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

cp=requests.get(f"{API}/products/MLM49608224",headers=HJ,timeout=15).json()
print("CPID:",cp.get("name"),"status:",cp.get("status"),"domain:",cp.get("domain_id"))
color=None; brand=None
for a in (cp.get("attributes") or []):
  if a.get("id") in ("COLOR","MAIN_COLOR") and not color: color=a.get("value_name")
  if a.get("id")=="BRAND": brand=a.get("value_name")
print("brand:",brand,"color:",color)

# Find correct leaf category from existing item under this CPID
it=requests.get(f"{API}/products/MLM49608224/items?limit=5",headers=HJ,timeout=12).json()
items=it.get("results",[])
cats=set([i.get("category_id") for i in items[:5] if i.get("category_id")])
print("leaf cats from existing items:",cats)
cat_to_use = list(cats)[0] if cats else "MLM59800"
print("Using cat:",cat_to_use)

title=cp.get("name","")[:60]
payload={
  "catalog_listing": True,
  "catalog_product_id": "MLM49608224",
  "category_id": cat_to_use,
  "price": 2399,
  "currency_id": "MXN",
  "available_quantity": 1,
  "listing_type_id": "gold_pro",
  "condition": "new",
  "title": title,
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\nPUBLISH MLM49608224: {r.status_code}")
print(r.text[:1500])
