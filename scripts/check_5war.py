import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
items=["MLM2910768333","MLM2910806845","MLM5337919270","MLM5337919282","MLM5337919290"]
for iid in items:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,status,sub_status,catalog_product_id,available_quantity,title",headers=H).json()
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=H).json()
    print(f"\n{iid} '{g.get('title','')[:60]}'")
    print(f"  st={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} cpid={g.get('catalog_product_id')}")
    print(f"  price=${g.get('price')} | PTW=${p.get('price_to_win')} status={p.get('status')} sharing={p.get('competitors_sharing_first_place')}")
