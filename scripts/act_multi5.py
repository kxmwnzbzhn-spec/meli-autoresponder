import os,json,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5300550156"
# Try relist with just listing_type_id (minimal)
r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json={"listing_type_id":"gold_pro"})
print(f"RELIST_MIN http={r.status_code} {r.text[:300]}")
if r.status_code>=300:
    # try with just quantity=1
    r2=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json={"listing_type_id":"gold_pro","quantity":1})
    print(f"RELIST_Q1 http={r2.status_code} {r2.text[:300]}")
time.sleep(2)
# Now set qty=5/color via PUT
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"POST_RELIST st={g.get('status')} qty={g.get('available_quantity')}")
new_vrs=[{"id":v["id"],"available_quantity":5} for v in g.get("variations",[])]
if new_vrs:
    pu=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"variations":new_vrs})
    print(f"SET_QTY http={pu.status_code} {pu.text[:300]}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"FINAL st={g2.get('status')} total_qty={g2.get('available_quantity')}")
for v in g2.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')}")
