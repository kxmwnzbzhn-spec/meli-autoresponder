import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2950827361"
g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
print(f"{iid}: pre status={g.get('status')} price={g.get('price')} '{(g.get('title') or '')[:40]}'")
if g.get("status")=="active":
    requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15); time.sleep(0.4)
r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
print(f"  close http={r2.status_code}")
g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
print(f"post: status={g2.get('status')}")
