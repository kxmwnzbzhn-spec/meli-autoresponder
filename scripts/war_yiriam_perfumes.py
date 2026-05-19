#!/usr/bin/env python3
"""War Yiriam — max-up agresivo:
- Si winning: subir a (low_comp - 1) capped at CEILING
- Si competing/losing: bajar a ptw-1 capped at FLOOR
- Si no hay competidor: mantener (no tocar)
Self-retrigger ~70s después del workflow para anti-throttle GH cron.
"""
import os,time,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

# Per-item floor (no bajar de aquí)
FLOOR_OVERRIDE={
  "MLM5363034834":349,
}

# Per-item ceiling (no subir de aquí, default 9999)
CEILING_OVERRIDE={
  # Locks específicos si necesitas tope estricto
  # "MLMxxx": 999,
}

ITEMS=[
  "MLM5291774150","MLM5291785036","MLM2909183147","MLM2916942827",
  "MLM2940047221","MLM5363034834","MLM5363034838","MLM2940047227","MLM5363034842",
  "MLM2940047233","MLM5363023022",
  "MLM5363147400","MLM5363034850","MLM5363023026","MLM5363034852","MLM5363147404",
  "MLM2940047245","MLM5363147408","MLM5363023032","MLM5363147410","MLM5363034856",
  "MLM5363147416","MLM2940047249","MLM5363147422","MLM5363034860",
  "MLM2940662359","MLM5364336572","MLM5364336602",
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
        title=(g.get("title") or "")[:25]
        cpid=g.get("catalog_product_id")
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
        ceil=CEILING_OVERRIDE.get(iid,9999)

        # Reactivate paused-with-stock
        if st=="paused" and qty>0:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            acts.append(f"REACT {iid} http={r.status_code}")
            if r.status_code<300: st="active"
        # Reactivate paused-no-stock con qty=1
        if st=="paused" and qty==0:
            requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
            time.sleep(0.3)
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            acts.append(f"REACT_QTY {iid} qty=1 http={r2.status_code}")
            if r2.status_code<300: st="active"

        if st!="active":
            continue

        # PTW v2 to know winning/competing state
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        ptw=p.get("price_to_win")
        ptw_st=(p.get("status") or "").lower()

        target=None
        reason=""

        if ptw_st=="winning":
            # Buscar low_comp via /products/{cpid}/items
            low_comp=None
            if cpid:
                try:
                    pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
                    results=pr.get("results") or pr.get("listings") or []
                    comps=[]
                    for rr in results:
                        rid=rr.get("item_id") or rr.get("id")
                        rp=rr.get("price")
                        rst=(rr.get("status") or "active").lower()
                        rq=rr.get("available_quantity",1)
                        if rid and rid!=iid and rp and rst=="active" and rq>0:
                            comps.append(rp)
                    comps.sort()
                    if comps:
                        low_comp=comps[0]
                except: pass
            if low_comp:
                # Subir a low_comp - 1 (max-up), cap ceiling
                t=int(low_comp)-1
                target=min(t,ceil)
                target=max(target,floor)
                reason=f"winning low_comp={low_comp} → ${target}"
            else:
                # Sin competencia → mantener
                reason=f"winning sin comp → hold ${cur}"
        elif ptw_st in ("competing","losing","sharing_first_place"):
            if ptw:
                target=max(int(ptw)-1, floor)
                target=min(target, ceil)
                reason=f"{ptw_st} ptw={ptw} → ${target}"
            else:
                reason=f"{ptw_st} sin ptw → hold"
        else:
            # under_review, not_listed, etc → skip
            reason=f"st={ptw_st} skip"

        if target is not None and target != cur:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            acts.append(f"{iid} '{title}' ${cur}→${target} ({reason}) http={r.status_code}")
        else:
            acts.append(f"{iid} '{title}' hold ${cur} ({reason})")
        time.sleep(0.4)
    except Exception as e:
        acts.append(f"ERR {iid}: {e}")

print(f"war-yiriam: {len(acts)} actions")
for a in acts: print(f"  {a}")
