import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM2940047221",headers=H,timeout=10).json()
print(f"pre: price=${g.get('price')} status={g.get('status')}")
r=requests.put(f"{API}/items/MLM2940047221",headers=HJ,json={"price":799},timeout=15)
print(f"  →$799 http={r.status_code}")
import time; time.sleep(1)
p=requests.get(f"{API}/items/MLM2940047221/price_to_win?version=v2",headers=H,timeout=10).json()
print(f"PTW: {p.get('status')}")
