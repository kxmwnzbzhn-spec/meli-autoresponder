"""Prueba token YC_NEW con la APP NUEVA."""
import os, requests, json
APP_ID=os.environ["MELI_APP_ID_NEW"]
APP_SECRET=os.environ["MELI_APP_SECRET_NEW"]
RT=os.environ.get("MELI_REFRESH_TOKEN_YC_NEW")
print(f"APP_ID={APP_ID}  RT_len={len(RT) if RT else 0}  RT_prefix={(RT or '')[:14]}")
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT})
print(f"HTTP {r.status_code}")
j=r.json()
if "access_token" in j:
    print(f"OK access={j['access_token'][:18]}...  new_refresh={(j.get('refresh_token') or '')[:18]}...")
    at=j["access_token"]
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {at}"}).json()
    print(f"  cuenta: uid={me.get('id')} nick={me.get('nickname')} email={me.get('email')}")
else:
    print(json.dumps(j, indent=2)[:400])
