import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for IID in ["MLM5511720082","MLM3014067125","MLM5510679006"]:
  g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"\n{IID}: {g.get('title','')[:50]} ${g.get('price')} status={g.get('status')} qty={g.get('available_quantity')}")
  for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
    requests.put(f"{API}/items/{IID}",headers=HJ,json=action,timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"  → {g2.get('status')} {g2.get('sub_status')} qty={g2.get('available_quantity')}")
