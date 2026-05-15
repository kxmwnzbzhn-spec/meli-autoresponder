import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5347886456"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE st={g.get('status')} qty={g.get('available_quantity')}")
if g.get("available_quantity")!=1 or g.get("status")!="active":
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","available_quantity":1})
    print(f"SET visible=1 http={r.status_code}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER st={g2.get('status')} qty={g2.get('available_quantity')}")
