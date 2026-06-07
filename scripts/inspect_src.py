import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
g=requests.get(f"{API}/items/MLM2976325463",headers=H,timeout=15).json()
print(json.dumps({
    "title":g.get("title"),
    "category_id":g.get("category_id"),
    "price":g.get("price"),
    "attributes":g.get("attributes"),
    "variations":g.get("variations"),
}, ensure_ascii=False, indent=2)[:5000])
