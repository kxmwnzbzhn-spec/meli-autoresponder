"""Forzar available_quantity=1 en todos los items active de Raymundo."""
import os, requests, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID=me["id"]
print(f"Cuenta: {me.get('nickname')}")

ids=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    b=rr.get("results",[])
    if not b: break
    ids.extend(b); offset+=50
    if offset>=rr.get("paging",{}).get("total",0): break

print(f"Active items: {len(ids)}")
fixed=0; ok=0; err=0
for iid in ids:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,available_quantity",headers=H,timeout=10).json()
    qty=g.get("available_quantity",0)
    if qty>1:
        rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":1},timeout=15)
        if rp.status_code==200:
            fixed+=1
            print(f"  💾 {iid}: {qty} → 1 | {(g.get('title') or '')[:50]}")
        else:
            err+=1
            print(f"  ❌ {iid}: HTTP {rp.status_code} {rp.text[:120]}")
    else:
        ok+=1
    time.sleep(0.15)
print(f"\nForzados a qty=1: {fixed} | Ya en 1: {ok} | Errores: {err}")
