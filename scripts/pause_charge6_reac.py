import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
# Pausar las 3 reacondicionadas Charge 6
for iid in ["MLM2911241921","MLM2911205487","MLM2911241939"]:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
    print(f"PAUSE {iid} http={r.status_code}")
