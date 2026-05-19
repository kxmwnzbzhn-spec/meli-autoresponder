#!/usr/bin/env python3
"""Reactivar TODOS los paused de Yiriam excepto DO_NOT_REACTIVATE."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

DO_NOT_REACTIVATE={
  "MLM5353056250",
  "MLM2909179597",
  "MLM5291788552",
  "MLM5291776046",
  "MLM5291772440",
  "MLM2909183135",
  "MLM2909179599",
  "MLM5363147396",
  "MLM5363023018",
}

T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

# Lista paused
items=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    items.extend(res)
    if len(res)<50 or offset>500: break
    offset+=50

print(f"Total paused: {len(items)}")
print(f"DO_NOT_REACTIVATE: {len(DO_NOT_REACTIVATE)}")

# 2 pasadas para KVS errors
for pass_n in (1,2):
    ok=err=skip=0
    print(f"\n=== PASS {pass_n} ===")
    for iid in items:
        if iid in DO_NOT_REACTIVATE:
            skip+=1; continue
        try:
            g=requests.get(f"{API}/items/{iid}",headers=H,timeout=8).json()
            st=g.get("status"); qty=g.get("available_quantity",0); sub=g.get("sub_status") or []
            if st=="active":
                continue
            if st!="paused":
                continue
            # Si qty=0 (out_of_stock), set qty=1 antes
            if qty==0:
                requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=10)
                time.sleep(0.2)
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=12)
            if r.status_code<300:
                ok+=1
                print(f"  REACT {iid} http={r.status_code}")
            else:
                err+=1
                print(f"  FAIL {iid} http={r.status_code} {r.text[:120]}")
            time.sleep(0.25)
        except Exception as e:
            err+=1; print(f"  ERR {iid}: {e}")
    print(f"  ok={ok} skip(DNR)={skip} err={err}")
    if err==0 and pass_n==1: break
    time.sleep(3)

# Recount
time.sleep(2)
r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=1",headers=H,timeout=15).json()
total_active=r.get("paging",{}).get("total",0)
print(f"\nFINAL active: {total_active}")
