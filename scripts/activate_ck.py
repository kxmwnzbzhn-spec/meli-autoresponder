import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM="MLM2976325463"
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
print(f"  title={g.get('title')}")

payload={"status":"active"}
if (g.get("available_quantity") or 0)<1:
    payload["available_quantity"]=1
rr=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=payload,timeout=15)
print(f"[ACTIVATE] HTTP {rr.status_code}: {rr.text[:400]}")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[AFTER] status={g2.get('status')} qty={g2.get('available_quantity')}")
print(f"Permalink: {g2.get('permalink')}")
