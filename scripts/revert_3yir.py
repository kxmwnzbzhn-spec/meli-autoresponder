import os,json,requests
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
TY=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT_Y}).json()["access_token"]
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}
YIR=["MLM5291785036","MLM5291788562","MLM2923681279"]
for iid in YIR:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HY,json={"status":"paused"})
    print(f"PAUSE {iid} http={r.status_code} {r.text[:150]}")
