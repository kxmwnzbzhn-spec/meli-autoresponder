import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM2967805809"
g=requests.get(f"{API}/items/{IID}?attributes=id,title,status,sub_status,available_quantity,sold_quantity",headers=H,timeout=15).json()
print(f"PRE: {g}")

# If paused → activate. If active → just set qty=1
if g.get("status")=="paused":
  p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":1},timeout=20)
  print(f"qty=1: {p1.status_code} {p1.text[:200]}")
  p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"active"},timeout=20)
  print(f"active: {p2.status_code} {p2.text[:200]}")
elif g.get("status")=="active":
  p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":1},timeout=20)
  print(f"qty=1: {p1.status_code} {p1.text[:200]}")

g2=requests.get(f"{API}/items/{IID}?attributes=id,title,status,sub_status,available_quantity",headers=H,timeout=15).json()
print(f"\nPOST: {g2}")
