import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM2935286615",headers=H,timeout=10).json()
cur=g.get("price"); print(f"pre: ${cur} status={g.get('status')}")
if cur and cur>899:
    r=requests.put(f"{API}/items/MLM2935286615",headers=HJ,json={"price":899},timeout=15)
    print(f"  ${cur}→$899 http={r.status_code}")
else:
    print(f"  cur ${cur} <= $899, sin cambio")
