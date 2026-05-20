"""Reactivar los 15 items"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

ITEMS=[
  "MLM5363023022","MLM2940047227","MLM5291785036","MLM2940047233",
  "MLM2940047221","MLM2940662359","MLM5363034838","MLM5291774150",
  "MLM2916942827","MLM2909183147","MLM5363034852","MLM5364336572",
  "MLM5364336602","MLM5291774160","MLM5291786710",
]

for pass_n in (1,2):
    print(f"\n=== PASS {pass_n} ===")
    ok=err=skip=0
    for iid in ITEMS:
        try:
            g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
            st=g.get("status"); qty=g.get("available_quantity",0)
            if st=="active":
                skip+=1; print(f"  SKIP {iid} (active)"); continue
            if st=="closed":
                skip+=1; print(f"  SKIP {iid} (closed)"); continue
            if qty==0:
                requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=10)
                time.sleep(0.3)
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            if r.status_code<300:
                ok+=1; print(f"  REACT {iid} http={r.status_code}")
            else:
                err+=1; print(f"  FAIL {iid} http={r.status_code} {r.text[:100]}")
            time.sleep(0.25)
        except Exception as e:
            err+=1; print(f"  ERR {iid}: {e}")
    print(f"  ok={ok} skip={skip} err={err}")
    if err==0 and pass_n==1: break
    time.sleep(3)
