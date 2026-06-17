import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

IID="MLM2911241921"
# Try with auth
ra=requests.get(f"{API}/items/{IID}",headers=H,timeout=15)
print(f"AUTH GET: {ra.status_code}")
print(ra.text[:600])
print()

# Try without auth (public)
rp=requests.get(f"{API}/items/{IID}",timeout=15)
print(f"PUBLIC GET: {rp.status_code}")
print(rp.text[:600])
print()

# Try alternative id query
ra2=requests.get(f"{API}/items?ids={IID}",headers=H,timeout=15)
print(f"BATCH GET: {ra2.status_code}")
print(ra2.text[:800])
