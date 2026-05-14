import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
for iid in ["MLM2910768333","MLM2910806845"]:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":349})
    print(f"{iid} SET $349 http={r.status_code}")
