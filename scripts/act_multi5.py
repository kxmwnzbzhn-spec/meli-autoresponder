import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5300550156"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE st={g.get('status')} qty={g.get('available_quantity')} price=${g.get('price')}")
vrs=g.get("variations",[])
new_vrs=[{"id":v["id"],"available_quantity":5,"price":v.get("price") or g.get("price",299)} for v in vrs]
relist_body={"variations":new_vrs,"listing_type_id":g.get("listing_type_id") or "gold_pro"}
r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json=relist_body)
print(f"RELIST http={r.status_code} {r.text[:400]}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER st={g2.get('status')} sub={g2.get('sub_status')} total_qty={g2.get('available_quantity')}")
for v in g2.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')}")
