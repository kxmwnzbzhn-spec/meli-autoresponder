import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5705924452"
g=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status,title",headers=H,timeout=10).json()
print(f"BEFORE: {g.get('status')} | {g.get('title','?')[:60]}",flush=True)
if g.get("status")=="active":
    pr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"paused"},timeout=10).json()
    print(f"paused: {pr.get('status')}",flush=True)
cr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"closed"},timeout=10).json()
print(f"closed: {cr.get('status')} err={cr.get('error','')}",flush=True)
