import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5363034834"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=price,status,title",headers=H).json()
print(f"current ${g.get('price')} st={g.get('status')} '{(g.get('title') or '')[:50]}'")
if g.get("price",0)<349 and g.get("status")=="active":
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":349})
    print(f"  raised to $349 http={r.status_code}")
