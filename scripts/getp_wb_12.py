import os,requests,json
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
WB=["MLM5265893750","MLM5309659262","MLM2908793361","MLM2916649417","MLM2916897121","MLM2908818183","MLM2916908777","MLM2916672247","MLM2916676513","MLM2916908753","MLM2916921559","MLM2916700919"]
prices={}
for iid in WB:
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=price,title",headers=H).json()
    prices[iid]={"price":p.get("price"),"title":(p.get("title") or "")[:50]}
print("PRICES:"+json.dumps(prices))
