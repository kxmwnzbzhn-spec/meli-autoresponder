import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5300550156"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE st={g.get('status')} sub={g.get('sub_status')} total_qty={g.get('available_quantity')}")
vrs=g.get("variations",[])
new_vrs=[]
for v in vrs:
    new_vrs.append({"id":v["id"],"available_quantity":5})
# Single PUT: activate + set variations
r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","variations":new_vrs})
print(f"UPDATE http={r.status_code} {r.text[:250]}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER st={g2.get('status')} sub={g2.get('sub_status')} total_qty={g2.get('available_quantity')}")
for v in g2.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')} vid={v.get('id')}")
