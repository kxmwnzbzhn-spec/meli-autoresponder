import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

items=["MLM2910768333","MLM2910806845"]
for iid in items:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,status,sub_status",headers=H).json()
    print(f"BEFORE {iid}: price=${g.get('price')} st={g.get('status')}")
    # try price to win for context
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=H).json()
    print(f"  ptw={p.get('price_to_win')} status={p.get('status')}")
    # bring price down to $349 immediately to recover
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":349})
    print(f"  SET $349 http={r.status_code} {r.text[:200]}")
