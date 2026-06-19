import os, requests, time
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
  g=requests.get(f"{API}/items/{IID}?attributes=id,title,status,sub_status,available_quantity,price",headers=H,timeout=15).json()
  print(f"PRE: status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} price={g.get('price')}")
  for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
    p=requests.put(f"{API}/items/{IID}",headers=HJ,json=action,timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"POST: status={g2.get('status')} sub={g2.get('sub_status')} qty={g2.get('available_quantity')}")
