import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM2940047233",headers=H,timeout=10).json()
print(f"pre: status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
r=requests.put(f"{API}/items/MLM2940047233",headers=HJ,json={"available_quantity":1},timeout=15)
print(f"  qty=1 http={r.status_code} body={r.text[:200]}")
g2=requests.get(f"{API}/items/MLM2940047233",headers=H,timeout=10).json()
print(f"post: qty={g2.get('available_quantity')}")
