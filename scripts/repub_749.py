import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2910880749"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"BEFORE st={g.get('status')} sub={g.get('sub_status')} price=${g.get('price')} qty={g.get('available_quantity')} title={(g.get('title') or '')[:60]}")
# Activate if needed + set price 599 + qty 1
body={"status":"active","price":599,"available_quantity":1}
r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body)
print(f"UPDATE http={r.status_code} {r.text[:250]}")
if r.status_code>=400:
    # try relist
    rl=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=H,json={"price":599,"quantity":1,"listing_type_id":g.get('listing_type_id') or 'gold_pro'})
    print(f"RELIST http={rl.status_code} {rl.text[:250]}")
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print(f"AFTER st={g2.get('status')} sub={g2.get('sub_status')} price=${g2.get('price')} qty={g2.get('available_quantity')}")
