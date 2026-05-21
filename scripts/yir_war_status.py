#!/usr/bin/env python3
"""Status del catalog war Yiriam — usa PTW v2 (detecta fantasmas Lider Platino).
Reporta winning/competing/losing real + arregla competing/losing a ptw-2."""
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

print(f"Yiriam (YC_NEW uid={uid}) active: {len(items)}\n")
print(f"{'item':<16} {'cur':>6} {'ptw':>7} {'estado':<12} accion")
win=comp=reindex=nocpid=0; fixes=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:16]
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR); ceil=CEILING_OVERRIDE.get(iid,9999)
        if not cpid:
            nocpid+=1; print(f"{iid:<16} {cur:>6} {'-':>7} {'sin_cpid':<12} - '{title}'"); continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        st=(p.get("status") or "").lower(); ptw=p.get("price_to_win")
        if st=="not_listed":
            reindex+=1; print(f"{iid:<16} {cur:>6} {'-':>7} {'REINDEX':<12} bump '{title}'"); continue
        if st in ("winning","sharing_first_place"):
            win+=1; print(f"{iid:<16} {cur:>6} {str(ptw):>7} {'GANANDO':<12} hold '{title}'")
        elif st in ("competing","losing"):
            comp+=1
            if ptw:
                t=max(int(ptw)-2,floor); t=min(t,ceil)
                if t<cur:
                    requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":t},timeout=15); fixes+=1
                    print(f"{iid:<16} {cur:>6}→${t} {str(ptw):>7} {'PERDIENDO':<12} CLAIM '{title}'")
                else:
                    print(f"{iid:<16} {cur:>6} {str(ptw):>7} {'PERDIENDO':<12} floor=${floor} '{title}'")
            else:
                print(f"{iid:<16} {cur:>6} {'-':>7} {st:<12} sin_ptw '{title}'")
        else:
            print(f"{iid:<16} {cur:>6} {str(ptw):>7} {st:<12} '{title}'")
        time.sleep(0.25)
    except Exception as e:
        print(f"  {iid}: ERR {e}")

print(f"\n=== RESUMEN WAR YIRIAM ===")
print(f"  Active: {len(items)} | GANANDO: {win} | PERDIENDO(fix): {comp} | REINDEX: {reindex} | sin_cpid: {nocpid}")
print(f"  Claims aplicados: {fixes}")
