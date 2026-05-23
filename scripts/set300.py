import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM2952660425",headers=H,timeout=10).json()
print(f"pre: ${g.get('price')} status={g.get('status')}")
r=requests.put(f"{API}/items/MLM2952660425",headers=HJ,json={"price":300},timeout=15)
print(f"  →$300 http={r.status_code} {('' if r.status_code<300 else r.text[:120])}")
