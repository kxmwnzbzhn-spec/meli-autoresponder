import os, json, requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2910457917"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print("CUR:",{k:g.get(k) for k in ["id","price","original_price","catalog_listing","status","sub_status","variations"]})
# Try price-only
p=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":549})
print("price-only:",p.status_code,p.text[:300])
# Try with original_price
p=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":549,"original_price":768})
print("with orig:",p.status_code,p.text[:300])
