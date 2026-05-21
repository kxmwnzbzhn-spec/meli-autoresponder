#!/usr/bin/env python3
"""Detalle de NO-ganadores Yiriam: separa losing / competing / sharing_first_place.
Muestra cur, ptw, low_ext + competidor real."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
FLOOR_OVERRIDE={"MLM5363034834":349,"MLM2940047227":349}
CEILING_OVERRIDE={"MLM5363034838":899}

T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
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

buckets={"winning":[],"sharing_first_place":[],"competing":[],"losing":[],"not_listed":[],"otro":[]}
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:30]
        if not cpid: continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        st=(p.get("status") or "otro").lower(); ptw=p.get("price_to_win")
        # low_ext
        pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
        ext=[]
        for r2 in (pr.get("results") or []):
            rid=r2.get("item_id") or r2.get("id"); rp=r2.get("price")
            rst=(r2.get("status") or "active").lower(); rq=r2.get("available_quantity",1)
            if rid and rid!=iid and rp and rst=="active" and rq>0: ext.append(rp)
        ext.sort()
        low_ext=ext[0] if ext else None
        rec={"id":iid,"cur":cur,"ptw":ptw,"low_ext":low_ext,"title":title,
             "floor":FLOOR_OVERRIDE.get(iid)}
        buckets.get(st, buckets["otro"]).append(rec)
        time.sleep(0.25)
    except Exception as e:
        print(f"ERR {iid}: {e}")

def show(name, lst):
    print(f"\n### {name.upper()} ({len(lst)}) ###")
    for r in lst:
        fl=f" floor=${r['floor']}" if r['floor'] else ""
        print(f"  {r['id']} cur=${r['cur']} ptw=${r['ptw']} low_ext=${r['low_ext']}{fl} '{r['title']}'")

show("PERDIENDO (losing)", buckets["losing"])
show("COMPARTIENDO 1er lugar (sharing)", buckets["sharing_first_place"])
show("COMPITIENDO (competing)", buckets["competing"])
show("not_listed/reindex", buckets["not_listed"])
print(f"\n=== GANANDO LIMPIO: {len(buckets['winning'])} ===")
