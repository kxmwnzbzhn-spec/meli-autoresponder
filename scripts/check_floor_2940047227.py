import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM2940047227",headers=H,timeout=10).json()
cur=g.get("price"); st=g.get("status")
print(f"MLM2940047227 status={st} cur=${cur}")
if cur and cur<349:
    r=requests.put(f"{API}/items/MLM2940047227",headers=HJ,json={"price":349},timeout=15)
    print(f"  bump to $349: http={r.status_code}")
else:
    print(f"  cur ${cur} ya >= $349, sin cambio")
