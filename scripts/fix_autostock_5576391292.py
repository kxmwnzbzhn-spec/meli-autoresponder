import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5576391292"
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=10).json()
print(f"BEFORE: status={g.get('status')} qty={g.get('available_quantity')} sub={g.get('sub_status')} price=${g.get('price')} title={g.get('title','?')[:60]}",flush=True)

# Reactivate + set qty=3 as buffer to prevent MELI closing on qty=0
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"active","available_quantity":3},timeout=15).json()
print(f"AFTER: status={r.get('status')} qty={r.get('available_quantity')} err={r.get('error','')}",flush=True)
if r.get("error"):
    print(f"  err: {json.dumps(r)[:400]}",flush=True)
