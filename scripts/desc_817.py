import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
# Get OLD desc
old=requests.get(f"https://api.mercadolibre.com/items/MLM2910806817/description",headers={"Authorization":f"Bearer {T}"}).json()
desc=old.get("plain_text") or ""
print(f"old desc len={len(desc)}")
if desc:
    r=requests.put("https://api.mercadolibre.com/items/MLM5354755946/description",headers=H,json={"plain_text":desc})
    if r.status_code>=300:
        r=requests.post("https://api.mercadolibre.com/items/MLM5354755946/description",headers=H,json={"plain_text":desc})
    print(f"desc set http={r.status_code} {r.text[:200]}")
