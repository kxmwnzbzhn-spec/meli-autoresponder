import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2916897225"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE: status={g.get('status')} sub={g.get('sub_status')} title={(g.get('title') or '')[:60]}")
# pause first
r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
print("PAUSE http=",r1.status_code,r1.text[:150])
# close
r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"})
print("CLOSE http=",r2.status_code,r2.text[:200])
# verify
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER: status={g2.get('status')} deleted={g2.get('deleted')}")
