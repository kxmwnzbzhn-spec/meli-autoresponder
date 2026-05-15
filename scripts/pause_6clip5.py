import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
items=["MLM2910457977","MLM2910457991","MLM2910768361","MLM2910457983","MLM2910880769","MLM2910806853"]
for iid in items:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,sub_status,title",headers=H).json()
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
    print(f"{iid} '{(g.get('title') or '')[:50]}' was={g.get('status')} → http={r.status_code}")
