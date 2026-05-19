import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
g=requests.get(f"{API}/items/MLM5291786738",headers=H,timeout=10).json()
print(f"pre: status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
if g.get("status")=="active":
    r1=requests.put(f"{API}/items/MLM5291786738",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  pause http={r1.status_code}")
    time.sleep(0.5)
r2=requests.put(f"{API}/items/MLM5291786738",headers=HJ,json={"status":"closed"},timeout=15)
print(f"  close http={r2.status_code} body={r2.text[:200]}")
time.sleep(0.5)
g2=requests.get(f"{API}/items/MLM5291786738",headers=H,timeout=10).json()
print(f"post: status={g2.get('status')}")
