import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2910806845"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE st={g.get('status')} price=${g.get('price')} title={(g.get('title') or '')[:55]}")
r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":399})
print(f"SET $399 http={r.status_code} {r.text[:200] if r.status_code>=300 else ''}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=price,status",headers=H).json()
print(f"AFTER price=${g2.get('price')} status={g2.get('status')}")
