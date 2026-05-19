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

print(f"Total active: {len(items)}\n")
print(f"{'item':<16} {'cur':>6} {'status':<22} {'ptw':>6} {'low_c':>8}  title")

losing=[]
sharing=[]
winning=0
for iid in items:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=8).json()
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:32]
        if not cpid:
            print(f"{iid:<16} {str(cur):>6} {'no-cpid':<22}")
            continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=8).json()
        st=(p.get("status") or "").lower()
        ptw=p.get("price_to_win") or ""
        low_c=""
        try:
            pr=requests.get(f"{API}/products/{cpid}/items?limit=15",headers=H,timeout=8).json()
            comps=[r["price"] for r in (pr.get("results") or []) if (r.get("item_id") or r.get("id"))!=iid and r.get("price")]
            comps.sort()
            if comps: low_c=comps[0]
        except: pass
        print(f"{iid:<16} {str(cur):>6} {st:<22} {str(ptw):>6} {str(low_c):>8}  {title}")
        if st=="winning": winning+=1
        elif "sharing" in st: sharing.append((iid,cur,ptw,low_c,title,cpid))
        elif st in ("competing","losing"): losing.append((iid,cur,ptw,low_c,title,cpid))
        time.sleep(0.2)
    except Exception as e:
        print(f"  ERR {iid}: {e}")

print(f"\n=== RESUMEN ===")
print(f"Winning: {winning}")
print(f"Sharing first place: {len(sharing)}")
print(f"Competing/Losing: {len(losing)}")

print(f"\n=== SHARING ===")
for iid,cur,ptw,low_c,t,cpid in sharing:
    print(f"  {iid} ${cur} ptw=${ptw} low_c=${low_c}  '{t}'")
print(f"\n=== LOSING ===")
for iid,cur,ptw,low_c,t,cpid in losing:
    print(f"  {iid} ${cur} ptw=${ptw} low_c=${low_c}  '{t}'")
