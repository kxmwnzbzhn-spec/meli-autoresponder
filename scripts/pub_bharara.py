import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Forzar qty alto para no quedarse en 0 entre ventas
for IID,QTY in [("MLM5525982716",100),("MLM3034001565",100),("MLM3034025531",50)]:
  g=requests.get(f"{API}/items/{IID}?attributes=id,status,available_quantity,sold_quantity",headers=H,timeout=15).json()
  print(f"\n{IID}: pre status={g.get('status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")
  if g.get("status") not in ("active","paused"): continue
  if g.get("status")=="paused":
    requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":QTY},timeout=20)
    requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"active"},timeout=20)
  else:
    requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":QTY},timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,available_quantity",headers=H,timeout=15).json()
  print(f"  → status={g2.get('status')} qty={g2.get('available_quantity')}")
