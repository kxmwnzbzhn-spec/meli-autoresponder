import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Find ASVA items in category MLM456032 (esoteric perfumes) from Alchemia
sid=1668713481
sr=requests.get(f"{API}/users/{sid}/items/search?category=MLM456032&limit=20",headers=H,timeout=15).json()
ids=sr.get("results",[])
print("found",len(ids),"items in MLM456032")
for iid in ids[:5]:
  it=requests.get(f"{API}/items/{iid}?attributes=id,title,price,available_quantity,category_id,attributes,catalog_product_id,family_name,status",headers=H,timeout=10).json()
  print(f"  {iid}: cat={it.get('category_id')} price={it.get('price')} cpid={it.get('catalog_product_id')} family={it.get('family_name')} title={it.get('title')[:60]}")
