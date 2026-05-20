#!/usr/bin/env python3
"""War Yiriam V4 — FIX bug FORCE DROP reputation win.
Si PTW v2 dice winning → confiar en MELI. NO dropear aunque cur > low_ext.
Solo max-up hasta low_ext-5 si hay headroom real.
Si competing/losing → ptw-2.
"""
import os, time, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

# PAUSED_LOCK: items que NO se reactivan ni tocan (el usuario los pausó manual)
PAUSED_LOCK={
  "MLM5363023022","MLM2940047227","MLM5291785036","MLM2940047233",
  "MLM2940047221","MLM2940662359","MLM5363034838","MLM5291774150",
  "MLM2916942827","MLM2909183147","MLM5363034852","MLM5364336572",
  "MLM5364336602","MLM5291774160","MLM5291786710",
}

FLOOR_OVERRIDE={"MLM5363034834":349,"MLM2940047227":349}
CEILING_OVERRIDE={"MLM5363034838":899}

ITEMS=[
  "MLM5291774150","MLM5291785036","MLM2909183147","MLM2916942827",
  "MLM2940047221","MLM5363034834","MLM5363034838","MLM2940047227","MLM5363034842",
  "MLM2940047233","MLM5363023022",
  "MLM5363147400","MLM5363034850","MLM5363023026","MLM2943550725","MLM5363147404",
  "MLM2940047245","MLM5363147408","MLM5363023032","MLM5363147410","MLM5363034856",
  "MLM5363147416","MLM2940047249","MLM5363147422","MLM5363034860","MLM5353056250",
  "MLM2940662359","MLM5364336572","MLM5364336602",
  "MLM5291774160","MLM5291786710","MLM5291786706","MLM5291788562",
]

T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

acts=[]
for iid in ITEMS:
    if iid in PAUSED_LOCK:
        acts.append(f"LOCKED {iid} skip"); continue
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
        if not g.get("id"): continue
        st=g.get("status"); qty=g.get("available_quantity",0); cur=g.get("price")
        title=(g.get("title") or "")[:22]
        cpid=g.get("catalog_product_id")
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
        ceil=CEILING_OVERRIDE.get(iid,9999)

        if st=="paused" and qty>0:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            acts.append(f"REACT {iid} http={r.status_code}")
            if r.status_code<300: st="active"
        if st=="paused" and qty==0:
            requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
            time.sleep(0.3)
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            acts.append(f"REACT_QTY {iid} http={r2.status_code}")
            if r2.status_code<300: st="active"
        if st!="active": continue
        if not cpid:
            acts.append(f"{iid} '{title}' sin_cpid")
            continue

        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        ptw=p.get("price_to_win"); ptw_st=(p.get("status") or "").lower()

        low_ext=None
        try:
            pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
            results=pr.get("results") or pr.get("listings") or []
            xc=[]
            for rr in results:
                rid=rr.get("item_id") or rr.get("id")
                rp=rr.get("price")
                rst=(rr.get("status") or "active").lower()
                rq=rr.get("available_quantity",1)
                if rid and rid!=iid and rp and rst=="active" and rq>0:
                    xc.append(rp)
            xc.sort()
            if xc: low_ext=xc[0]
        except: pass

        target=None; reason=""
        if ptw_st=="not_listed":
            # forzar reindex con pequeño bump (alternancia +/-1 cada corrida)
            bump=cur-1 if cur>floor else cur+1
            target=bump
            reason=f"not_listed reindex_bump → ${target}"
        elif ptw_st in ("winning","sharing_first_place"):
            # CONFIAR EN MELI: solo max-up si hay headroom. NUNCA dropear.
            if low_ext:
                can_up=int(low_ext)-5
                can_up=min(can_up,ceil); can_up=max(can_up,floor)
                if can_up > cur:
                    target=can_up
                    reason=f"max-up winning low_ext={low_ext} (-5) → ${target}"
                else:
                    reason=f"winning cur=${cur} hold (low_ext={low_ext})"
            else:
                reason=f"winning sin comp → hold ${cur}"
        elif ptw_st in ("competing","losing"):
            if ptw:
                target=max(int(ptw)-2, floor); target=min(target,ceil)
                reason=f"{ptw_st} ptw={ptw}-2 → ${target}"
            elif low_ext:
                target=max(int(low_ext)-2,floor); target=min(target,ceil)
                reason=f"{ptw_st} via low_ext={low_ext}-2 → ${target}"
            else:
                reason=f"{ptw_st} sin info hold"
        else:
            reason=f"st={ptw_st} skip"

        if target is not None and target != cur:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            acts.append(f"{iid} '{title}' ${cur}→${target} [{reason}] http={r.status_code}")
        else:
            acts.append(f"{iid} '{title}' hold ${cur} [{reason}]")
        time.sleep(0.25)
    except Exception as e:
        acts.append(f"ERR {iid}: {e}")

print(f"war-yiriam-v4: {len(acts)} actions")
for a in acts: print(f"  {a}")
