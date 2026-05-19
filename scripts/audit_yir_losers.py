import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]
off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break
print(f"Yiriam active: {len(ids)}\n")
print(f"{'ID':<18} {'$':>5} {'PTW':>5} {'Δ':>5} {'STATUS':<11} TITLE")
losing=[]
for iid in ids:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=price,title,catalog_listing,catalog_product_id",headers=H).json()
    if not g.get("catalog_listing"): continue
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=H).json()
    cur=g.get("price"); ptw=p.get("price_to_win"); status=p.get("status","-")
    title=(g.get("title") or "")[:40]
    if not ptw:
        print(f"{iid:<18} {cur or 0:>5} {'-':>5} {'-':>5} {status:<11} {title}")
        continue
    delta=cur-ptw
    flag="" if status=="winning" and delta<=0 else " ❌"
    if status!="winning": losing.append((iid,cur,ptw,status,title))
    print(f"{iid:<18} {cur or 0:>5} {ptw:>5} {delta:>+5} {status:<11} {title}{flag}")

print(f"\n=== LOSING/COMPETING ({len(losing)}) ===")
for r in losing: print(f"  {r}")
