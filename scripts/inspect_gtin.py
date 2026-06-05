import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
p=requests.get(f"{API}/products/MLM61262890",headers=H,timeout=10).json()
print("Attributes:")
for a in (p.get("attributes") or []):
    print(f"  {a.get('id')}: {a.get('value_name')}  vid={a.get('value_id')}")
