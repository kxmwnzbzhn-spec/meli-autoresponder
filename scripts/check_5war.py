import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
for iid in ["MLM2910768333","MLM2910806845","MLM5337919270","MLM5337919282","MLM5337919290"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,status,catalog_listing",headers=H).json()
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=H).json()
    print(f"{iid} ${g.get('price')} st={g.get('status')} | PTW=${p.get('price_to_win')} cat_status={p.get('status')}")
