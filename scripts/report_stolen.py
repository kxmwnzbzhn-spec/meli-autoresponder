import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Dump full /returns response to find action URL
cid,rid=5530358522,143755516
rr=requests.get(f"{API}/marketplace/v2/claims/{cid}/returns",headers=HJ,timeout=20)
print(json.dumps(rr.json(),indent=2,default=str)[:6000])
