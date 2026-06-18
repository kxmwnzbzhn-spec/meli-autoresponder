import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5516269150"
g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,catalog_product_id",headers=H,timeout=15).json()
print(f"PRE: {g}")
p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"paused"},timeout=20)
print(f"PAUSE: {p.status_code} {p.text[:200]}")
g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status",headers=H,timeout=15).json()
print(f"POST: {g2}")
