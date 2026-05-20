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

# Check + re-pause si están active
ok=err=skip=0
for iid in ITEMS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    st=g.get("status")
    if st=="paused":
        skip+=1
        continue
    if st=="closed":
        skip+=1
        continue
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    if r.status_code<300:
        ok+=1
        print(f"  RE-PAUSE {iid} (era {st}) http={r.status_code}")
    else:
        err+=1
        print(f"  FAIL {iid} http={r.status_code}")
    time.sleep(0.2)

print(f"\nResultado: re-paused={ok} already_paused={skip} err={err}")
