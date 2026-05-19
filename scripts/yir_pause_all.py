#!/usr/bin/env python3
"""Pausar TODOS los items active de Yiriam (panic stop por hoy).
Reactivate_6am los reactiva mañana 6 AM Mérida."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

# Lista TODOS los active
items=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    items.extend(res)
    if len(res)<50 or offset>500: break
    offset+=50

print(f"Active pre-pause: {len(items)}")
ok=err=0
for iid in items:
    try:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
        if r.status_code<300:
            ok+=1
            print(f"  PAUSE {iid} http={r.status_code}")
        else:
            err+=1
            print(f"  FAIL  {iid} http={r.status_code} {r.text[:120]}")
        time.sleep(0.25)
    except Exception as e:
        err+=1
        print(f"  ERR  {iid}: {e}")

# Reconteo
time.sleep(2)
r2=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50",headers=H,timeout=15).json()
active_post=r2.get("paging",{}).get("total",0)
print(f"\nResultado: ok={ok} err={err}")
print(f"Active post-pause: {active_post}")
