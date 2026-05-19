#!/usr/bin/env python3
"""Yiriam ops v2:
1) Finalizar MLM2909183167 + MLM5291762790
2) Auditoría completa: TODOS los items active de Yiriam, su estado de buy box
3) Por cada perdiendo, mostrar competidor y por qué (precio, reputación, envío)
"""
import os,time,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

print("=== FINALIZAR ===")
for iid in ["MLM2909183167","MLM5291762790"]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    st_pre=g.get("status"); cur=g.get("price"); qty=g.get("available_quantity")
    print(f"  {iid} pre={st_pre} qty={qty} price={cur}")
    if st_pre=="active":
        r1=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
        print(f"    PAUSE http={r1.status_code}")
        time.sleep(0.4)
    r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
    print(f"    CLOSE http={r2.status_code}")
    time.sleep(0.3)

# Get Yiriam uid
me=requests.get(f"{API}/users/me",headers=H).json()
uid=me.get("id")
print(f"\n=== AUDIT BUY BOX (Yiriam uid={uid}) ===")

# Get all active items
nick=me.get("nickname")
items=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    items.extend(res)
    if len(res)<50 or offset>500: break
    offset+=50

print(f"Total active: {len(items)}")
print()
print(f"{'item':<16} {'cur':>6} {'status':<10} {'ptw':>6} {'low_c':>7}  {'gap':>5}  title")

losing=[]
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:30]
        if not cpid:
            continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        st=(p.get("status") or "").lower()
        ptw=p.get("price_to_win") or ""
        # Get low_comp
        low_c=""
        try:
            pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
            results=pr.get("results") or []
            comps=[r for r in results if (r.get("item_id") or r.get("id"))!=iid and r.get("price")]
            comps.sort(key=lambda x: x["price"])
            if comps: low_c=comps[0]["price"]
        except: pass
        gap=""
        if low_c and cur:
            gap=f"{int(cur-low_c):+d}"
        line=f"{iid:<16} {str(cur):>6} {st:<10} {str(ptw):>6} {str(low_c):>7}  {gap:>5}  {title}"
        print(line)
        if st in ("competing","losing"):
            losing.append((iid, cur, ptw, low_c, title, cpid))
        time.sleep(0.25)
    except Exception as e:
        print(f"  ERR {iid}: {e}")

print(f"\n=== PERDIENDO BUY BOX: {len(losing)} items ===")
for iid,cur,ptw,low_c,title,cpid in losing:
    print(f"\n{iid} '{title}' cpid={cpid}")
    print(f"  nuestro=${cur}  ptw=${ptw}  low_comp=${low_c}")
    # Detallar todos los competidores
    try:
        pr=requests.get(f"{API}/products/{cpid}/items?limit=10",headers=H,timeout=10).json()
        for r in (pr.get("results") or [])[:5]:
            rid=r.get("item_id") or r.get("id")
            rp=r.get("price"); ship=r.get("shipping",{}).get("free_shipping","?")
            sel=r.get("seller_id"); sold=r.get("sold_quantity",0)
            mark=" ← NOSOTROS" if rid==iid else ""
            print(f"    {rid}  ${rp}  ship_free={ship}  sold={sold}{mark}")
    except Exception as e:
        print(f"  competitors err: {e}")
