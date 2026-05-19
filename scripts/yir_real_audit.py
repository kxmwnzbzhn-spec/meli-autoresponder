#!/usr/bin/env python3
"""Audit REAL via /products/{cpid}/items.
Compara nuestro precio vs TODOS los competidores. Identifica:
- Donde NO somos el más barato (verdadero losing)
- Donde empatamos en primer lugar
- Y baja a low_real-2 para asegurar buy box
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

print(f"=== Yiriam active: {len(items)} ===\n")
print(f"{'item':<16} {'cur':>6} {'low_real':>8} {'2nd':>6}  state                 action")

actions=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:18]
        if not cpid:
            print(f"{iid:<16} {str(cur):>6} {'no_cpid':>8} {'-':>6}  -                      '{title}'")
            continue
        # Lista TODOS competidores active in-stock
        pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
        results=pr.get("results") or pr.get("listings") or []
        comps=[]  # (item_id, price, sold)
        for r in results:
            rid=r.get("item_id") or r.get("id")
            rp=r.get("price"); rst=(r.get("status") or "active").lower()
            rq=r.get("available_quantity",1)
            if rid and rp and rst=="active" and rq>0:
                comps.append((rid,rp,r.get("sold_quantity",0)))
        comps.sort(key=lambda x: x[1])
        # ¿Somos el más barato?
        if not comps:
            state="solos"; action="-"
        else:
            lowest=comps[0]
            if lowest[0]==iid:
                # Somos #1; ver si hay empate
                same_price=[c for c in comps if c[1]==cur and c[0]!=iid]
                if same_price:
                    state=f"SHARING (empate con {len(same_price)})"
                    floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
                    ceil=CEILING_OVERRIDE.get(iid,9999)
                    target=max(cur-2,floor); target=min(target,ceil)
                    if target<cur:
                        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                        action=f"BREAK_TIE ${cur}→${target} http={r.status_code}"
                        actions+=1
                    else:
                        action=f"empate pero floor={floor} bloquea"
                else:
                    state="WINNING #1"; action="-"
            else:
                # NO somos los más baratos
                state=f"LOSING (#{[c[0] for c in comps].index(iid)+1 if iid in [c[0] for c in comps] else '?'})"
                floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR)
                ceil=CEILING_OVERRIDE.get(iid,9999)
                target=max(int(lowest[1])-2,floor); target=min(target,ceil)
                if target<cur:
                    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
                    action=f"CLAIM ${cur}→${target} http={r.status_code}"
                    actions+=1
                else:
                    action=f"low=${lowest[1]} pero floor={floor} bloquea"
        sec=str(comps[1][1]) if len(comps)>=2 else "-"
        low=str(comps[0][1]) if comps else "-"
        print(f"{iid:<16} {str(cur):>6} {low:>8} {sec:>6}  {state:<22} {action} '{title}'")
        time.sleep(0.3)
    except Exception as e:
        print(f"ERR {iid}: {e}")

print(f"\nAcciones tomadas: {actions}")
