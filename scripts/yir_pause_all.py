#!/usr/bin/env python3
"""Pausar TODOS los active de Yiriam."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

# Pausar 2 pasadas para garantizar (KVS 409s a veces)
for pass_n in (1,2):
    items=[]
    offset=0
    while True:
        r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
        res=r.get("results") or []
        items.extend(res)
        if len(res)<50 or offset>500: break
        offset+=50
    print(f"\n=== PASS {pass_n}: active={len(items)} ===")
    if not items:
        print("Nada que pausar.")
        break
    ok=err=0
    for iid in items:
        try:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
            if r.status_code<300: ok+=1
            else: err+=1; print(f"  FAIL {iid} {r.status_code}")
            time.sleep(0.25)
        except Exception as e:
            err+=1; print(f"  ERR {iid}: {e}")
    print(f"  ok={ok} err={err}")
    time.sleep(3)

# Recuento final
time.sleep(2)
r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=1",headers=H,timeout=15).json()
print(f"\nFINAL active: {r.get('paging',{}).get('total',0)}")
