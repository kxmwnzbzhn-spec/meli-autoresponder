import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5300550156"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
# Try relist with full variations object including all attribute_combinations
vrs=g.get("variations",[])
formatted=[]
for v in vrs:
    formatted.append({
        "id":v["id"],
        "price":v.get("price") or g.get("price") or 299,
        "available_quantity":5,
        "attribute_combinations":v.get("attribute_combinations",[]),
        "picture_ids":v.get("picture_ids",[])
    })
body={"variations":formatted,"listing_type_id":g.get("listing_type_id") or "gold_pro"}
r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json=body)
print(f"RELIST_FULL http={r.status_code} {r.text[:500]}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER st={g2.get('status')} qty={g2.get('available_quantity')}")
for v in g2.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')}")
