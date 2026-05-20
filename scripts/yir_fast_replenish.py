#!/usr/bin/env python3
"""Fast replenish Yiriam — detecta paused/out_of_stock y reactiva con qty=1.
NO toca precios (eso lo hace war_yiriam_perfumes).
Diseñado para correr cada ~30s con self-retrigger."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

DO_NOT_REACTIVATE={
  "MLM5291786710",
  "MLM5291774160",
  "MLM5364336602",
  "MLM5364336572",
  "MLM5363034852",
  "MLM2909183147",
  "MLM2916942827",
  "MLM5291774150",
  "MLM5363034838",
  "MLM2940662359",
  "MLM2940047221",
  "MLM2940047233",
  "MLM5291785036",
  "MLM2940047227",
  "MLM5363023022",
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

items=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    items.extend(res)
    if len(res)<50 or offset>500: break
    offset+=50

actions=[]
t0=time.time()
for iid in items:
    if iid in DO_NOT_REACTIVATE: continue
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=8).json()
        st=g.get("status"); sub=g.get("sub_status",[]) or []
        if st!="paused": continue
        if "out_of_stock" not in sub: continue
        r1=requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=10)
        r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=10)
        actions.append(f"REPL {iid} qty1+act http=({r1.status_code},{r2.status_code})")
    except Exception as e:
        actions.append(f"ERR {iid}: {e}")

elapsed=time.time()-t0
print(f"yir-fast-replenish: scanned={len(items)} actions={len(actions)} t={elapsed:.1f}s")
for a in actions: print(f"  {a}")
