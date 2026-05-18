#!/usr/bin/env python3
"""War Yiriam — 25 items activos. Compite contra externos (PTW-1)."""
import os,time,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

ITEMS=[
  "MLM5291774150","MLM5291785036",
  "MLM2940047221","MLM5363034834","MLM5363034838","MLM2940047227","MLM5363034842",
  "MLM5363023018","MLM2940047233","MLM5363147396","MLM5363023022",
  "MLM5363147400","MLM5363034850","MLM5363023026","MLM5363034852","MLM5363147404",
  "MLM2940047245","MLM5363147408","MLM5363023032","MLM5363147410","MLM5363034856",
  "MLM5363147416","MLM2940047249","MLM5363147422","MLM5363034860",
  "MLM2940662359","MLM5364336572","MLM2940673601","MLM5364336602",
]

def tok():
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
T=tok()
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

acts=[]
for iid in ITEMS:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
        if not g.get("id"): continue
        st=g.get("status"); qty=g.get("available_quantity",0); cur=g.get("price")
        title=(g.get("title") or "")[:30]
        if st=="paused" and qty>0:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            acts.append(f"REACT {iid} http={r.status_code}")
            if r.status_code<300: st="active"
        if st=="paused" and qty==0:
            r1=requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
            time.sleep(0.3)
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            acts.append(f"REACT_QTY {iid} qty=1 http={r2.status_code}")
            if r2.status_code<300: st="active"
        if st!="active": continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=15).json()
        ptw=p.get("price_to_win")
        if not ptw: continue
        target=max(int(ptw)-1,MIN_FLOOR)
        if target!=cur:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            acts.append(f"{iid} '{title}' ${cur}→${target} ptw={ptw} http={r.status_code}")
        time.sleep(0.4)
    except Exception as e:
        acts.append(f"ERR {iid}: {e}")

print(f"war-yiriam: {len(acts)} actions")
for a in acts: print(f"  {a}")
