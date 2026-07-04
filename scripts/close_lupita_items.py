import os, json, requests

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LUPITA"]

# refresh
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
  timeout=25).json()
AT=r["access_token"]
NEW_RT=r["refresh_token"]
print(f"NEW_RT_LUPITA: {NEW_RT}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for ID in ["MLM5633114458","MLM5633089236"]:
    print(f"\n=== {ID} ===",flush=True)
    g=requests.get(f"https://api.mercadolibre.com/items/{ID}",headers=H,timeout=10).json()
    print(f"  before: status={g.get('status')} qty={g.get('available_quantity')} title={g.get('title','?')[:60]}",flush=True)
    if g.get("status")=="active":
        p=requests.put(f"https://api.mercadolibre.com/items/{ID}",headers=H,json={"status":"paused"},timeout=10).json()
        print(f"  paused: status={p.get('status')} err={p.get('error','')}",flush=True)
    c=requests.put(f"https://api.mercadolibre.com/items/{ID}",headers=H,json={"status":"closed"},timeout=10).json()
    print(f"  closed: status={c.get('status')} err={c.get('error','')}",flush=True)
