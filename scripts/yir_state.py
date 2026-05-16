import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
YIR=["MLM5353056250","MLM2935286537","MLM2935286557","MLM5353056302","MLM2935286581","MLM2935286605","MLM2935274091","MLM2935286651","MLM5353056406","MLM2935286681","MLM2935286703","MLM2935298361"]
for iid in YIR:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    print(f"{iid} st={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')} price=${g.get('price')} '{(g.get('title') or '')[:35]}'")
