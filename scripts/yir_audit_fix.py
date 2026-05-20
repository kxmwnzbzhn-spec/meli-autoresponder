#!/usr/bin/env python3
"""Audit REAL Yiriam + fix perdedores.
- cur < low_ext → WINNING #1 (hold)
- cur == low_ext → empate → bajar a cur-3
- cur > low_ext → LOSING → bajar a low_ext-3 (respeta floor)
"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200
FLOOR_OVERRIDE={"MLM5363034834":349,"MLM2940047227":349}
CEILING_OVERRIDE={"MLM5363034838":899}

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

print(f"Active: {len(items)}\n")
print(f"{'item':<16} {'cur':>6} {'low_ext':>8} {'verdict':<14} action")
win=lose=tie=reindex=nocpid=0; fixes=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:18]
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR); ceil=CEILING_OVERRIDE.get(iid,9999)
        if not cpid:
            nocpid+=1; print(f"{iid:<16} {cur:>6} {'-':>8} {'no_cpid':<14} skip '{title}'"); continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        ptw_st=(p.get("status") or "").lower()
        pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
        results=pr.get("results") or []
        ext=[]
        for r2 in results:
            rid=r2.get("item_id") or r2.get("id"); rp=r2.get("price")
            rst=(r2.get("status") or "active").lower(); rq=r2.get("available_quantity",1)
            if rid and rid!=iid and rp and rst=="active" and rq>0: ext.append(rp)
        ext.sort()
        low_ext=ext[0] if ext else None
        if ptw_st=="not_listed":
            reindex+=1; print(f"{iid:<16} {cur:>6} {str(low_ext or '-'):>8} {'REINDEX':<14} bump '{title}'"); continue
        if low_ext is None:
            win+=1; print(f"{iid:<16} {cur:>6} {'-':>8} {'SOLO #1':<14} hold '{title}'"); continue
        if cur < low_ext:
            win+=1; print(f"{iid:<16} {cur:>6} {low_ext:>8} {'WIN #1':<14} hold (+${int(low_ext-cur)}) '{title}'")
        elif cur == low_ext:
            tie+=1
            t=max(cur-3,floor); t=min(t,ceil)
            if t<cur:
                requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":t},timeout=15); fixes+=1
                print(f"{iid:<16} {cur:>6}→${t} {low_ext:>8} {'TIE→break':<14} '{title}'")
            else:
                print(f"{iid:<16} {cur:>6} {low_ext:>8} {'TIE floor':<14} '{title}'")
        else:
            lose+=1
            t=max(int(low_ext)-3,floor); t=min(t,ceil)
            if t<cur:
                requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":t},timeout=15); fixes+=1
                print(f"{iid:<16} {cur:>6}→${t} {low_ext:>8} {'LOSE→DROP':<14} '{title}'")
            else:
                print(f"{iid:<16} {cur:>6} {low_ext:>8} {'LOSE floor':<14} (floor=${floor}) '{title}'")
        time.sleep(0.25)
    except Exception as e:
        print(f"  {iid}: ERR {e}")

print(f"\n=== RESUMEN ===")
print(f"  Active: {len(items)} | WIN: {win} | LOSE: {lose} | TIE: {tie} | REINDEX: {reindex} | sin_cpid: {nocpid}")
print(f"  Fixes aplicados: {fixes}")
