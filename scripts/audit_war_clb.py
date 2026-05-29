"""Audit del war de Claribel: por cada catalog listing, ver status y por qué pierde."""
import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]

# All active items
ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    ids.extend(res)
    if len(res)<50 or off>1000: break
    off+=50
print(f"\nactive items: {len(ids)}")

stats={"win":0,"share":0,"comp":0,"lose":0,"not_listed":0,"nocpid":0,"other":0}
rows=[]
for iid in ids:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    if g.get("status")!="active": continue
    cpid=g.get("catalog_product_id")
    if not cpid: stats["nocpid"]+=1; continue
    cur=g.get("price")
    title=(g.get("title") or "")[:35]
    sku=None
    for a in (g.get("attributes") or []):
        if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    pst=(p.get("status") or "").lower(); ptw=p.get("price_to_win")
    # buy box winner
    pr=requests.get(f"{API}/products/{cpid}/items?limit=10",headers=H,timeout=10).json()
    others=[]
    for rr in (pr.get("results") or []):
        rid=rr.get("item_id") or rr.get("id"); rp=rr.get("price")
        if rid and rid!=iid and rp:
            others.append((rid,rp))
    others.sort(key=lambda x:x[1])
    low_ext=others[0][1] if others else None
    
    if pst=="winning": stats["win"]+=1
    elif pst=="sharing_first_place": stats["share"]+=1
    elif pst=="competing": stats["comp"]+=1
    elif pst=="losing": stats["lose"]+=1
    elif pst=="not_listed": stats["not_listed"]+=1
    else: stats["other"]+=1
    
    rows.append((pst,iid,cpid,sku,cur,ptw,low_ext,title))

print(f"\n=== STATS ===")
for k,v in stats.items(): print(f"  {k}: {v}")

print(f"\n=== LOSING / COMPETING (ours vs winner) ===")
losing=[r for r in rows if r[0] in ("losing","competing","not_listed")]
for pst,iid,cpid,sku,cur,ptw,low_ext,title in losing:
    diff = cur - low_ext if low_ext else None
    print(f"  [{pst:<10}] {iid} sku={sku!s:<10} ours=${cur} ptw={ptw} low_ext={low_ext} diff={diff} | {title}")

print(f"\n=== WINNING ===")
for pst,iid,cpid,sku,cur,ptw,low_ext,title in rows:
    if pst not in ("winning","sharing_first_place"): continue
    print(f"  [{pst:<10}] {iid} sku={sku!s:<10} ours=${cur} low_ext={low_ext} | {title}")
