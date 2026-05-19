#!/usr/bin/env python3
"""Audit + recovery agresivo del buy box Yiriam:
- Para cada item active con CPID:
  - Si winning: hold
  - Si sharing_first_place: bajar a ptw-2 (rompe empate)
  - Si competing/losing: bajar a ptw-2 (claim, no solo -1)
- Respeta FLOOR_OVERRIDE
- Reporta TODO el estado
"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

FLOOR_OVERRIDE={
  "MLM5363034834":349,
}
CEILING_OVERRIDE={
  "MLM5363034838":899,
}

T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

items=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    items.extend(res)
    if len(res)<50 or offset>500: break
    offset+=50

print(f"=== Yiriam active: {len(items)} ===\n")
print(f"{'item':<16} {'cur':>6} {'ptw':>6} {'status':<20} action")

stats={"winning":0,"sharing":0,"competing":0,"losing":0,"other":0,"no_cpid":0}
actions=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id")
        title=(g.get("title") or "")[:20]
        if not cpid:
            stats["no_cpid"]+=1
            print(f"{iid:<16} {str(cur):>6} {'':>6} {'no_cpid':<20} -")
            continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        st=(p.get("status") or "").lower()
        ptw=p.get("price_to_win")
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
        ceil=CEILING_OVERRIDE.get(iid,9999)

        act="-"
        if st=="winning":
            stats["winning"]+=1
            act=f"WIN '{title}'"
        elif "sharing" in st:
            stats["sharing"]+=1
            if ptw:
                target=max(int(ptw)-2, floor)
                target=min(target,ceil)
                if target<cur:
                    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                    act=f"SHARING ${cur}→${target} (ptw={ptw}-2) http={r.status_code} '{title}'"
                    actions+=1
                else:
                    act=f"SHARING ptw={ptw} pero floor={floor} bloquea '{title}'"
            else:
                act=f"SHARING sin ptw '{title}'"
        elif st in ("competing","losing"):
            stats[st]+=1
            if ptw:
                target=max(int(ptw)-2, floor)
                target=min(target,ceil)
                if target<cur:
                    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                    act=f"CLAIM ${cur}→${target} (ptw={ptw}-2) http={r.status_code} '{title}'"
                    actions+=1
                else:
                    act=f"{st} ptw={ptw} pero floor={floor} bloquea '{title}'"
            else:
                act=f"{st} sin ptw '{title}'"
        else:
            stats["other"]+=1
            act=f"{st} '{title}'"
        print(f"{iid:<16} {str(cur):>6} {str(ptw or '-'):>6} {st:<20} {act}")
        time.sleep(0.25)
    except Exception as e:
        print(f"ERR {iid}: {e}")

print(f"\n=== STATS ===")
for k,v in stats.items(): print(f"  {k}: {v}")
print(f"Bajadas hechas: {actions}")
