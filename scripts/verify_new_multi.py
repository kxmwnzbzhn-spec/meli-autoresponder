import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
g=requests.get(f"https://api.mercadolibre.com/items/MLM5346655686",headers=H).json()
print(f"NEW MLM5346655686 st={g.get('status')} sub={g.get('sub_status')} total_qty={g.get('available_quantity')} title={(g.get('title') or '')[:60]}")
for v in g.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')} price=${v.get('price')} vid={v['id']}")
