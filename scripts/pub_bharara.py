import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
for IID in ["MLM5511732856","MLM3020492945"]:
  g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,available_quantity,catalog_product_id",headers=H,timeout=15).json()
  print(f"{IID}: {g}")
