import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
ITEM=os.environ["ITEM"]
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=15).json()
print(f"title: {g.get('title')}")
print(f"category_id: {g.get('category_id')}")
print(f"price: {g.get('price')}")
print(f"pictures: {len(g.get('pictures') or [])}")
for a in (g.get("attributes") or []):
    print(f"  {a.get('id')}: name='{a.get('value_name')}' id={a.get('value_id')}")
