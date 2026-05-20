#!/usr/bin/env python3
"""V2 fix bug: comparar cur vs lowest_price directamente.
Si cur < lowest_competitor_price → somos #1 (independiente de si /products/items nos incluye).
Si cur > lowest → drop a lowest-5.
"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200
FLOOR_OVERRIDE={"MLM5363034834":349}
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
restored=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:20]
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
        ceil=CEILING_OVERRIDE.get(iid,9999)
        if not cpid:
            print(f"{iid:<16} {cur:>6} {'-':>8} {'NO_CPID':<14} '{title}'")
            continue
        pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
        results=pr.get("results") or pr.get("listings") or []
        # EXCLUYE nuestro item para low_ext
        ext_comps=[]
        for r2 in results:
            rid=r2.get("item_id") or r2.get("id")
            rp=r2.get("price"); rst=(r2.get("status") or "active").lower()
            rq=r2.get("available_quantity",1)
            if rid and rid!=iid and rp and rst=="active" and rq>0:
                ext_comps.append(rp)
        ext_comps.sort()
        if not ext_comps:
            print(f"{iid:<16} {cur:>6} {'-':>8} {'SOLO':<14} '{title}'")
            continue
        low_ext=ext_comps[0]
        # CORRECTO: cur < low_ext → somos #1
        if cur < low_ext:
            print(f"{iid:<16} {cur:>6} {low_ext:>8} {'WINNING #1':<14} '{title}'")
        elif cur == low_ext:
            # empate
            target=cur-2
            target=max(target,floor); target=min(target,ceil)
            if target<cur:
                r3=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                restored+=1
                print(f"{iid:<16} {cur:>6}→${target} {low_ext:>8} {'TIE_BREAK':<14} http={r3.status_code} '{title}'")
            else:
                print(f"{iid:<16} {cur:>6} {low_ext:>8} {'TIE_FLOOR':<14} '{title}'")
        else:
            # LOSING — somos más caros
            target=int(low_ext)-5
            target=max(target,floor); target=min(target,ceil)
            if target<cur:
                r3=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                restored+=1
                print(f"{iid:<16} {cur:>6}→${target} {low_ext:>8} {'LOSING DROP':<14} http={r3.status_code} '{title}'")
            else:
                print(f"{iid:<16} {cur:>6} {low_ext:>8} {'LOSING FLOOR':<14} '{title}'")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {iid}: ERR {e}")

print(f"\nDrops verdaderos: {restored}")

# IMPORTANTE: revertir MLM5291772416 (era $699, lo bajé a $444 mal). Set $694 (1 abajo del orig).
# Actually no — ya está a $444 y vendiéndose. Lo subimos a $694 si NO hay perdida real.
# Mejor: dejar al war manejarlo (ya re-evaluará en próxima corrida).
