import os,json,requests,base64
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5300550156"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
vrs=g.get("variations",[])
print(f"Variations found: {len(vrs)}")
# Build new variations array preserving structure, setting qty=1
new_vrs=[]
per_color={}
for v in vrs:
    vd={"id":v["id"],"available_quantity":1}
    # keep price if exists at variation level
    if v.get("price"): vd["price"]=v["price"]
    new_vrs.append(vd)
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    per_color[color or v["id"]]=v["id"]
print("Setting qty=1 per variation:",json.dumps(per_color,ensure_ascii=False))
r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"variations":new_vrs})
print("UPDATE_QTY http=",r.status_code,r.text[:400])
# verify
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER total_qty={g2.get('available_quantity')} status={g2.get('status')}")
for v in g2.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')} vid={v.get('id')}")
