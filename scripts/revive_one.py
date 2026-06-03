import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM=os.environ.get("ITEM","MLM5233454100")
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} price={g.get('price')} inv={g.get('inventory_id')}")
print(f"  title={g.get('title')}")

qty=g.get("available_quantity") or 0
payload={"status":"active"}
if qty<1: payload["available_quantity"]=1

rp=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=payload,timeout=15)
print(f"\n[REACTIVATE payload={payload}] HTTP {rp.status_code}: {rp.text[:400]}")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"\n[AFTER] status={g2.get('status')} sub={g2.get('sub_status')} qty={g2.get('available_quantity')}")
print(f"Permalink: {g2.get('permalink')}")
