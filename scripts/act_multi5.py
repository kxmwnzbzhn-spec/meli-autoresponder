import os,json,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5300550156"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
vrs=g.get("variations",[])

# Try different field name: "quantity" instead of "available_quantity"
formatted=[{"id":v["id"],"price":v.get("price") or g.get("price",299),"quantity":5} for v in vrs]
body={"variations":formatted,"listing_type_id":g.get("listing_type_id") or "gold_pro"}
r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json=body)
print(f"RELIST_Q http={r.status_code} {r.text[:400]}")
if r.status_code>=300:
    # Try with just id + price (no qty)
    formatted2=[{"id":v["id"],"price":v.get("price") or g.get("price",299)} for v in vrs]
    body2={"variations":formatted2,"listing_type_id":g.get("listing_type_id") or "gold_pro"}
    r2=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json=body2)
    print(f"RELIST_NOQTY http={r2.status_code} {r2.text[:400]}")
time.sleep(2)
g3=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"NOW st={g3.get('status')} qty={g3.get('available_quantity')}")
# If active now, set qty via PUT
if g3.get("status")=="active":
    new_vrs=[{"id":v["id"],"available_quantity":5} for v in g3.get("variations",[])]
    pu=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"variations":new_vrs})
    print(f"PUT_QTY http={pu.status_code} {pu.text[:300]}")
g4=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"FINAL st={g4.get('status')} qty={g4.get('available_quantity')}")
for v in g4.get("variations",[]):
    color=""
    for c in v.get("attribute_combinations",[]):
        if c.get("id")=="COLOR": color=c.get("value_name")
    print(f"  {color}: qty={v.get('available_quantity')}")
