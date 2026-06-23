import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
for cid in [5530358522,5530353540]:
  c=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15).json()
  print(f"=== CLAIM {cid} ===")
  print("stage:",c.get("stage"),"status:",c.get("status"))
  print("resolution:",c.get("resolution"))
