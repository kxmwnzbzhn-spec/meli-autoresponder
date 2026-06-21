import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM3035213185"
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
print(f"PRE: status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")

# Try every recovery action
for action,label in [({"deleted":"false"},"undelete"),({"available_quantity":1},"qty=1"),({"status":"active"},"active")]:
  p=requests.put(f"{API}/items/{IID}",headers=HJ,json=action,timeout=20)
  print(f"  {label}: {p.status_code} {p.text[:250]}")

g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
print(f"POST: {g2}")
