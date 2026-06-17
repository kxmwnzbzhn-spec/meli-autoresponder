import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

def show(c,d=0):
  ci=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json()
  print(f"{'  '*d}{c} - {ci.get('name')}")
  for ch in ci.get("children_categories",[]):
    show(ch["id"],d+1)

show("MLM417671")
