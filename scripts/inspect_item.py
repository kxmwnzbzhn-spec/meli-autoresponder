import os, requests, json
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}
IID="MLM2969851475"
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
print(f"title: {g.get('title')}")
print(f"price: {g.get('price')}  status: {g.get('status')}  catalog_product_id: {g.get('catalog_product_id')}")
print(f"category: {g.get('category_id')}  listing_type: {g.get('listing_type_id')}")
print("attrs:")
for a in g.get('attributes',[])[:30]:
  print(f"  {a.get('id')}: {a.get('value_name')}")
cpid=g.get('catalog_product_id')
if cpid:
  cp=requests.get(f"https://api.mercadolibre.com/products/{cpid}",timeout=15).json()
  print(f"\n=== CPID {cpid} OFFICIAL ===")
  print("name:",cp.get("name"))
  print("status:",cp.get("status"))
  print("category_id:",cp.get("domain_id"),cp.get("category_id"))
  for a in cp.get("attributes",[])[:30]:
    print(f"  {a.get('id')}: {a.get('value_name')}")
  pics=cp.get("pictures") or []
  print(f"pictures: {len(pics)}")
  for p in pics[:5]: print("  ",p.get("url"))
