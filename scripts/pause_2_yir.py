import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
for iid in ["MLM5363147396","MLM5363023018"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,title,price",headers=H).json()
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
    print(f"{iid} '{(g.get('title') or '')[:45]}' ${g.get('price')} {g.get('status')} → http={r.status_code}")
    g2=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,sub_status",headers=H).json()
    print(f"  AFTER st={g2.get('status')} sub={g2.get('sub_status')}")
