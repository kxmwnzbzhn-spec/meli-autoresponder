import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Check + CLOSE/DELETE all 5
IIDS=["MLM5511027118","MLM3014079893","MLM5516269150","MLM5517826416"]
for IID in IIDS:
  g=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity,price",headers=H,timeout=15).json()
  print(f"\n{IID}: status={g.get('status')} qty={g.get('available_quantity')} sub={g.get('sub_status')} price={g.get('price')}")
  # Force close
  p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":0},timeout=20)
  p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"paused"},timeout=20)
  p3=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"closed"},timeout=20)
  p4=requests.put(f"{API}/items/{IID}",headers=HJ,json={"deleted":"true"},timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"  → status={g2.get('status')} sub={g2.get('sub_status')} qty={g2.get('available_quantity')}")
