import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
for iid in ["MLM2935447531","MLM2935447545","MLM5353156204","MLM2935587237","MLM2935587247","MLM2935587257"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=H).json()
    print(f"{iid} st={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} ${g.get('price')} ptw={p.get('price_to_win')} cat_status={p.get('status')}")
