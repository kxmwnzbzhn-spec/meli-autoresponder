import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5705924474"
g=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status,price,title",headers=H,timeout=10).json()
print(f"BEFORE: status={g.get('status')} price=${g.get('price')} title={g.get('title','?')[:60]}",flush=True)
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"price":499},timeout=15).json()
if r.get("error"):
    print(f"err: {r.get('message','?')} — trying details: {json.dumps(r)[:500]}",flush=True)
else:
    print(f"AFTER: price=${r.get('price')} status={r.get('status')}",flush=True)
