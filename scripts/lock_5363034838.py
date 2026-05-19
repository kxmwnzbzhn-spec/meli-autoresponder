import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
r=requests.put(f"{API}/items/MLM5363034838",headers=H,json={"price":899},timeout=15)
print(f"MLM5363034838 → $899 http={r.status_code}")
time.sleep(1)
H2={"Authorization":f"Bearer {T}"}
g=requests.get(f"{API}/items/MLM5363034838",headers=H2,timeout=10).json()
print(f"verified: price={g.get('price')} status={g.get('status')}")
