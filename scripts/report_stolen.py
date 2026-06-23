import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Search items in ASVA with "Alchemia" in title
sr=requests.get(f"{API}/users/1668713481/items/search?q=Alchemia&limit=10",headers=H,timeout=15).json()
ids=sr.get("results",[])
print("found",len(ids))
for iid in ids[:5]:
  it=requests.get(f"{API}/items/{iid}?include_attributes=all&attributes=id,title,price,available_quantity,category_id,catalog_product_id,family_name,status,listing_type_id,condition,shipping,sale_terms,attributes,description",headers=H,timeout=10).json()
  print(f"\n--- {iid} ---")
  print(f"  cat={it.get('category_id')} cpid={it.get('catalog_product_id')} price={it.get('price')} listing={it.get('listing_type_id')} status={it.get('status')}")
  print(f"  family={it.get('family_name')}")
  print(f"  title={it.get('title')}")
