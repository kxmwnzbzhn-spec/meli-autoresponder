"""Audit REAL via /products/{cpid}/items + PTW v2.
Reporta ganando/perdiendo/not_listed."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
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

print(f"Active: {len(items)}\n")
print(f"{'item':<16} {'cur':>6} {'low_ext':>8} {'PTW':<15} verdict")

stats={"winning":0,"losing":0,"not_listed":0,"no_cpid":0}
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:18]
        if not cpid:
            stats["no_cpid"]+=1
            print(f"{iid:<16} {cur:>6} {'-':>8} {'no_cpid':<15} -")
            continue
        # PTW
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        st=(p.get("status") or "").lower()
        # low_ext
        pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
        results=pr.get("results") or []
        comps=[]
        for r2 in results:
            rid=r2.get("item_id") or r2.get("id")
            rp=r2.get("price")
            if rid and rid!=iid and rp:
                comps.append(rp)
        comps.sort()
        low_ext=comps[0] if comps else None
        # Verdict real
        if st=="not_listed":
            stats["not_listed"]+=1
            verdict="REINDEX"
        elif st in ("winning","sharing_first_place"):
            stats["winning"]+=1
            verdict=f"WIN  +${int((low_ext or cur)-cur)}" if low_ext else "WIN solo"
        else:
            stats["losing"]+=1
            verdict=f"LOSE -${int(cur-(low_ext or cur))}"
        print(f"{iid:<16} {cur:>6} {str(low_ext or '-'):>8} {st:<15} {verdict}  '{title}'")
        time.sleep(0.25)
    except Exception as e:
        print(f"  {iid}: ERR {e}")

print(f"\n=== RESUMEN ===")
print(f"  Active total: {len(items)}")
print(f"  Ganando #1:   {stats['winning']}")
print(f"  Perdiendo:    {stats['losing']}")
print(f"  not_listed:   {stats['not_listed']}")
print(f"  Sin CPID:     {stats['no_cpid']}")
