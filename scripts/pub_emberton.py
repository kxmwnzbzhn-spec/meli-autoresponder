import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

IID="MLM5516466768"
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
print(f"id: {g.get('id')}")
print(f"title: {g.get('title')}")
print(f"price: ${g.get('price')}")
print(f"base_price: ${g.get('base_price')}")
print(f"original_price: ${g.get('original_price')}")
print(f"status: {g.get('status')}  sub: {g.get('sub_status')}")
print(f"condition: {g.get('condition')}")
print(f"permalink: {g.get('permalink')}")
# Pricing channels
pr=requests.get(f"{API}/items/{IID}/prices",headers=H,timeout=15)
print(f"\n/prices:",pr.status_code)
print(pr.text[:800])
