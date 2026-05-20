#!/usr/bin/env python3
"""FORCE WIN: Audit todos los items active de Yiriam.
Para cada uno: GET /products/{cpid}/items, ordenar por price asc.
Si NO somos el más barato, bajar a (lowest - 5).
Respeta FLOOR/CEILING.
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
dropped=0; held=0; nocomp=0; nocpid=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:25]
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
        ceil=CEILING_OVERRIDE.get(iid,9999)
        if not cpid:
            nocpid+=1
            print(f"  {iid:<16} cur={cur:>6}  NO_CPID  '{title}'")
            continue
        pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
        results=pr.get("results") or pr.get("listings") or []
        comps=[]
        for r2 in results:
            rid=r2.get("item_id") or r2.get("id")
            rp=r2.get("price"); rst=(r2.get("status") or "active").lower()
            rq=r2.get("available_quantity",1)
            if rid and rp and rst=="active" and rq>0:
                comps.append((rid,rp))
        comps.sort(key=lambda x: x[1])
        if not comps:
            nocomp+=1
            print(f"  {iid:<16} cur={cur:>6}  NO_COMP  '{title}'")
            continue
        lowest_id, lowest_price = comps[0]
        if lowest_id==iid:
            # Somos #1
            held+=1
            print(f"  {iid:<16} cur={cur:>6}  #1 (#2=${comps[1][1] if len(comps)>1 else '-'})  '{title}'")
        else:
            # NO somos #1 → drop a lowest - 5
            target=int(lowest_price)-5
            target=max(target,floor); target=min(target,ceil)
            if target>=cur:
                # piso bloquea
                print(f"  {iid:<16} cur={cur:>6}  LOSING low=${lowest_price} pero floor=${floor} bloquea  '{title}'")
            else:
                rp2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                dropped+=1
                print(f"  {iid:<16} cur={cur:>6}→${target}  LOSING low=${lowest_price} → DROP http={rp2.status_code}  '{title}'")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {iid}: ERR {e}")

print(f"\n=== RESUMEN ===")
print(f"  Items active: {len(items)}")
print(f"  Drops realizados: {dropped}")
print(f"  Ya #1 (hold): {held}")
print(f"  Sin competencia: {nocomp}")
print(f"  Sin CPID: {nocpid}")
