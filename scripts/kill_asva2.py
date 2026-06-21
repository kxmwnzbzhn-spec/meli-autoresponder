import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for IID in ["MLM3849137034","MLM2378087893"]:
  print(f"\n=== {IID} ===")
  g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
  print(f"  PRE: status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")
  
  # Try undelete first
  p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"deleted":"false"},timeout=20)
  print(f"  undelete: {p1.status_code} {p1.text[:300]}")
  
  # Try set qty
  p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":1},timeout=20)
  print(f"  qty=1: {p2.status_code} {p2.text[:300]}")
  
  # Try activate
  p3=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"active"},timeout=20)
  print(f"  active: {p3.status_code} {p3.text[:300]}")
  
  # Try paused
  p4=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"paused"},timeout=20)
  print(f"  paused: {p4.status_code} {p4.text[:300]}")
  
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"  POST: {g2}")
