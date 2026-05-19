#!/usr/bin/env python3
"""Reactivar los 18 items que se pausaron en el panic stop."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

ITEMS=[
  "MLM5291785036","MLM5291774150","MLM2909183147","MLM2916942827",
  "MLM5353056250","MLM5364336602","MLM5364336572","MLM5363034852",
  "MLM5363034842","MLM5363034838","MLM5363034834","MLM5363023022",
  "MLM2940664057","MLM2940664023","MLM2940662359","MLM2940047233",
  "MLM2940047227","MLM2940047221",
]

ok=err=skip=0
for iid in ITEMS:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        st=g.get("status"); qty=g.get("available_quantity",0)
        if st=="active":
            print(f"  SKIP {iid} (ya active)")
            skip+=1; continue
        if st!="paused":
            print(f"  SKIP {iid} (st={st})")
            skip+=1; continue
        if qty==0:
            requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
            time.sleep(0.3)
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        if r.status_code<300:
            ok+=1; print(f"  REACT {iid} http={r.status_code}")
        else:
            err+=1; print(f"  FAIL  {iid} http={r.status_code} {r.text[:100]}")
        time.sleep(0.3)
    except Exception as e:
        err+=1; print(f"  ERR {iid}: {e}")
print(f"\nReactivados: ok={ok} skip={skip} err={err}")
