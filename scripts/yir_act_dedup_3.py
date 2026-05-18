import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

TARGETS=["MLM2909183147","MLM2916942827","MLM5291772416"]

# Step 1: activate the 3 targets
print("=== STEP 1: Activate 3 targets ===")
target_info={}
for iid in TARGETS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if not g.get("id"):
        print(f"  ✗ {iid}: no data ({str(g)[:100]})"); continue
    st=g.get("status"); qty=g.get("available_quantity",0); cpid=g.get("catalog_product_id")
    sold=g.get("sold_quantity",0); title=(g.get("title") or "")[:50]
    target_info[iid]={"cpid":cpid,"sold":sold,"title":title,"status":st,"qty":qty}
    print(f"  {iid} st={st} qty={qty} sold={sold} cpid={cpid} '{title}'")
    if st=="paused":
        if qty<=0:
            r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1,"status":"active"},timeout=15)
        else:
            r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        print(f"    → ACTIVATE http={r.status_code}")
    elif st=="closed":
        r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=HJ,json={"price":int(g.get('price') or 500),"quantity":1,"listing_type_id":g.get("listing_type_id") or "gold_pro"},timeout=15)
        print(f"    → RELIST http={r.status_code} {r.text[:150]}")
        if r.status_code<300: target_info[iid]["new_id"]=r.json().get("id")
    elif st=="active":
        if qty!=1:
            r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
            print(f"    → qty=1 http={r.status_code}")
        else:
            print(f"    → ya active qty=1")

# Step 2: find duplicates en Yiriam por CPID
print("\n=== STEP 2: Check duplicates ===")
target_cpids={iid:info["cpid"] for iid,info in target_info.items() if info.get("cpid")}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]

# List ALL items (active+paused) and group by CPID
all_ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H,timeout=15).json()
        res=r.get("results",[])
        if not res: break
        all_ids+=res; off+=100
        if off>=r.get("paging",{}).get("total",0): break
print(f"  Total Yiriam items: {len(all_ids)}")

# Get cpid+sold+status of each
by_cpid={}
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    mg=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,catalog_product_id,sold_quantity,status",headers=H).json()
    for x in mg:
        b=x.get("body",{}) or {}
        cpid=b.get("catalog_product_id")
        if not cpid: continue
        by_cpid.setdefault(cpid,[]).append({"id":b["id"],"sold":b.get("sold_quantity",0) or 0,"status":b.get("status"),"title":(b.get("title") or "")[:40]})

# Step 3: For each target CPID, find duplicates and pause less-sold
print("\n=== STEP 3: Dedup per target CPID ===")
for iid,cpid in target_cpids.items():
    dups=by_cpid.get(cpid,[])
    if len(dups)<2:
        print(f"  {iid} cpid={cpid} — sin duplicados (solo 1 listing)")
        continue
    # Sort by sold desc, keep top
    dups.sort(key=lambda x:-x["sold"])
    keep=dups[0]
    print(f"  {iid} cpid={cpid} → {len(dups)} listings duplicadas")
    for d in dups: print(f"     {d['id']} sold={d['sold']} st={d['status']} '{d['title']}'")
    print(f"     KEEP: {keep['id']} (sold={keep['sold']})")
    for d in dups[1:]:
        if d["status"]=="paused":
            print(f"     SKIP {d['id']} (ya paused)"); continue
        r=requests.put(f"https://api.mercadolibre.com/items/{d['id']}",headers=HJ,json={"status":"paused"},timeout=15)
        print(f"     PAUSE {d['id']} (sold={d['sold']}) http={r.status_code}")
    time.sleep(0.3)

print("\n=== DONE ===")
