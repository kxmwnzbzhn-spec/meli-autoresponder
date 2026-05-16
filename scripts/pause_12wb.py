import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
WB=["MLM5265893750","MLM5309659262","MLM2908793361","MLM2916649417","MLM2916897121","MLM2908818183","MLM2916908777","MLM2916672247","MLM2916676513","MLM2916908753","MLM2916921559","MLM2916700919"]
for iid in WB:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,title",headers=H).json()
    if g.get("status")=="paused":
        print(f"{iid} already paused")
        continue
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
    print(f"PAUSE {iid} '{(g.get('title') or '')[:45]}' http={r.status_code}")
