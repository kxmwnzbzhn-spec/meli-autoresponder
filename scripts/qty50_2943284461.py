import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM2943284461",headers=H,timeout=10).json()
print(f"pre: status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')} logistic={g.get('shipping',{}).get('logistic_type')}")
print(f"  inventory_id={g.get('inventory_id')}")
r=requests.put(f"{API}/items/MLM2943284461",headers=HJ,json={"available_quantity":50},timeout=15)
print(f"  qty=50 http={r.status_code} body={r.text[:200]}")
time.sleep(1)
g2=requests.get(f"{API}/items/MLM2943284461",headers=H,timeout=10).json()
print(f"post: qty={g2.get('available_quantity')}")
