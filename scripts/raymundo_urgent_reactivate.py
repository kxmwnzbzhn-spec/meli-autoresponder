"""Reactivar AHORA todos los items pausados de Raymundo (one-shot rápido)."""
import os, requests, time, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID=me["id"]
ids=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
    b=rr.get("results",[])
    if not b: break
    ids.extend(b); offset+=50
    if offset>=rr.get("paging",{}).get("total",0): break
print(f"Pausados: {len(ids)}")
ok=0; fail=0
for iid in ids:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    if not g.get("catalog_listing"):
        print(f"  skip tradicional {iid}"); continue
    qty=g.get("available_quantity",0)
    body={"status":"active"}
    if qty==0: body["available_quantity"]=1
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
    if rp.status_code==200:
        ok+=1; print(f"  ▶️ {iid} qty={qty} → activo")
    else:
        fail+=1; print(f"  ❌ {iid}: {rp.status_code} {rp.text[:120]}")
    time.sleep(0.2)
print(f"\nOK: {ok} | Fallos: {fail}")
