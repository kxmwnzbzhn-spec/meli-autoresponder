"""Diagnostica + arregla 3 items Yiriam: 5363023022, 5363034834, 2940047227"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
FLOOR={"MLM5363034834":349,"MLM2940047227":349,"MLM5363023022":200}
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

for iid in ["MLM5363023022","MLM5363034834","MLM2940047227"]:
    print(f"\n=== {iid} ===")
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    st=g.get("status"); sub=g.get("sub_status"); qty=g.get("available_quantity"); cur=g.get("price")
    cpid=g.get("catalog_product_id"); health=g.get("health")
    print(f"  status={st} sub={sub} qty={qty} price=${cur} cpid={cpid} health={health}")
    floor=FLOOR.get(iid,200)
    # 1) Si paused → reactivar
    if st=="paused":
        if qty==0:
            requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=10); time.sleep(0.3)
        ra=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        print(f"  REACTIVAR http={ra.status_code}")
        time.sleep(1)
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        st=g.get("status"); cur=g.get("price")
    if st!="active":
        print(f"  ⚠ sigue {st}, no se puede competir")
        continue
    # 2) PTW
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    pst=p.get("status"); ptw=p.get("price_to_win")
    print(f"  PTW: {pst} ptw=${ptw}")
    if pst=="not_listed":
        # reindex bump
        bump=cur-1 if cur>floor else cur+1
        rb=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":bump},timeout=15)
        print(f"  REINDEX bump ${cur}→${bump} http={rb.status_code}")
    elif pst in ("competing","losing","sharing_first_place") and ptw:
        target=max(int(ptw)-2,floor)
        if target<cur:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            print(f"  CLAIM ${cur}→${target} (floor=${floor}) http={r.status_code}")
            time.sleep(1.2)
            p2=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
            print(f"  PTW post: {p2.get('status')}")
        else:
            print(f"  ⚠ ptw=${ptw} pero floor=${floor} bloquea — perdiendo por tu piso")
    else:
        print(f"  ✅ {pst} — ok")
