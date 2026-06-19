import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IIDS=["MLM5510952004","MLM5511027118","MLM3014079893","MLM5516269150","MLM5517826416"]
for IID in IIDS:
  print(f"\n=== {IID} ===")
  g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"PRE: status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')}")
  # Force qty=0 and pause
  p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":0},timeout=20)
  print(f"QTY=0: {p1.status_code} {p1.text[:200]}")
  p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"paused"},timeout=20)
  print(f"PAUSE: {p2.status_code} {p2.text[:200]}")
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"POST: {g2}")
