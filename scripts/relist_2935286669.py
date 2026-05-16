import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
r=requests.post(f"https://api.mercadolibre.com/items/MLM2935286669/relist",headers=H,json={"price":998,"quantity":1,"listing_type_id":"gold_pro"})
print(f"relist http={r.status_code} {r.text[:300]}")
if r.status_code<300:
    print(f"NEW_ID={r.json().get('id')}")
