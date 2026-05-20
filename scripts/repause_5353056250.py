import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM5353056250",headers=H,timeout=10).json()
print(f"pre: status={g.get('status')} price={g.get('price')}")
if g.get("status")=="active":
    r=requests.put(f"{API}/items/MLM5353056250",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  pause http={r.status_code}")
else:
    print(f"  ya {g.get('status')}, sin cambio")
g2=requests.get(f"{API}/items/MLM5353056250",headers=H,timeout=10).json()
print(f"post: status={g2.get('status')}")
