import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# SOLO status=paused — NUNCA closed, NUNCA deleted
for IID in ["MLM3035113159","MLM3035214061","MLM3035214059"]:
  g=requests.get(f"{API}/items/{IID}?attributes=id,status,available_quantity",headers=H,timeout=15).json()
  print(f"\n{IID} PRE: status={g.get('status')} qty={g.get('available_quantity')}")
  p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"paused"},timeout=20)
  print(f"  PAUSE: {p.status_code} {p.text[:200]}")
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
  print(f"  POST: {g2}")
