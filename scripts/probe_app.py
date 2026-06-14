import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID_NEW"]; CSEC=os.environ["MELI_APP_SECRET_NEW"]
print(f"[client_id] {CID}")

# Try client_credentials
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"client_credentials","client_id":CID,"client_secret":CSEC},timeout=15)
print(f"[client_credentials] HTTP {r.status_code}")
print(f"  body: {r.text[:400]}")

if r.status_code==200:
  AT=r.json().get("access_token")
  H={"Authorization":f"Bearer {AT}"}
  for url in [f"{API}/applications/{CID}",f"{API}/users/me",f"{API}/applications/me"]:
    rr=requests.get(url,headers=H,timeout=10)
    print(f"\n{url} -> HTTP {rr.status_code}")
    print(f"  body: {rr.text[:600]}")
