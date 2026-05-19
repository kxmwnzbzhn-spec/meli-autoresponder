import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2940673601"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE st={g.get('status')} sold={g.get('sold_quantity')} title={(g.get('title') or '')[:50]}")
# pause first
r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
print(f"PAUSE http={r1.status_code}")
time.sleep(2)
# close
r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"})
print(f"CLOSE http={r2.status_code} {r2.text[:200]}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,sub_status",headers=H).json()
print(f"AFTER st={g2.get('status')} sub={g2.get('sub_status')}")
