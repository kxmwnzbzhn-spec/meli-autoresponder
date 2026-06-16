import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5516466768"
p=requests.put(f"{API}/items/{IID}",headers=H,json={"price":1199},timeout=20)
print("PUT price 1199:",p.status_code,p.text[:500])

g=requests.get(f"{API}/items/{IID}?attributes=id,price,status,condition,title",headers=H,timeout=15).json()
print("now:",g)
