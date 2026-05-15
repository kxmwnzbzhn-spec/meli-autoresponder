import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5347886456"
r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused","available_quantity":0})
print(f"URGENT PAUSE {iid} http={r.status_code} {r.text[:200]}")
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"NOW st={g.get('status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")
