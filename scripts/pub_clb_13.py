import os, requests, time, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')}")

SKUS=[
 ("ELEC-010","JBL Go 4 Rojo",["MLM44710313","MLM45577570","MLM46998439","MLM47119316","MLM48666693","MLM58850976","MLM64389753"]),
 ("ELEC-027","JBL Go 4 Rosa",["MLM2019694299","MLM45530822","MLM45700101","MLM65831856"]),
 ("ELEC-009","JBL Go 4 Camuflaje",["MLM37361021","MLM43902928"]),
 ("ELEC-030","JBL Go 4 Aqua",["MLM61262890"]),
 ("ELEC-013","JBL Go 3 Negro",["MLM29147620","MLM37158857","MLM37197513","MLM44709174","MLM44709179","MLM44710730","MLM44728420","MLM44744958","MLM44799641","MLM46039390"]),
 ("ELEC-011","JBL Clip 5 Azul",["MLM37110751","MLM40329314","MLM58592190","MLM61825899"]),
 ("ELEC-012","JBL Clip 5 Morado",["MLM44573520","MLM44712007","MLM44714111","MLM45586155","MLM47145951","MLM49054893"]),
 ("ELEC-018","JBL Clip 5 Camuflaje",["MLM44712057","MLM44714150","MLM48157832","MLM58616124"]),
 ("ELEC-029","JBL Clip 5 Rosa",["MLM63875183","MLM64288232"]),
 ("ELEC-031","JBL Clip 5 Aqua",[]),  # discover below
 ("ELEC-021","Bose Soundlink Home Negro",["MLM49963786"]),
 ("ELEC-025","Bose Soundlink Home Silver",["MLM50131488"]),
 ("ELEC-014","Sony XB100 Negro",["MLM25912333"]),
]

# Discover Clip 5 Aqua CPID
def discover_cpid(query):
    r=requests.get(f"{API}/products/search",params={"site_id":"MLM","q":query,"status":"active"},headers=H,timeout=20).json()
    cpids=[]
    q=query.lower()
    for p in r.get("results",[])[:10]:
        name=(p.get("name") or "").lower()
        if "clip 5" in name and ("aqua" in name or "acqua" in name or "azul agua" in name):
            cpids.append(p["id"])
    return cpids
disc=discover_cpid("JBL Clip 5 Aqua")
print(f"\nClip 5 Aqua discovered: {disc[:3]}")
if disc:
    # update list in tuple
    new=[]
    for sku,name,cpids in SKUS:
        if sku=="ELEC-031": new.append((sku,name,disc[:3]))
        else: new.append((sku,name,cpids))
    SKUS=new

# Map Claribel existing items by CPID
print("\nMapping Claribel existing listings...")
existing={}  # cpid -> (item_id, status)
all_ids=set()
for st in ["active","paused","under_review","programmed","closed","inactive"]:
    scroll=None
    while True:
        p={"search_type":"scan","limit":100,"status":st}
        if scroll: p["scroll_id"]=scroll
        r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
        all_ids.update(r.get("results",[]))
        scroll=r.get("scroll_id")
        if not scroll or not r.get("results"): break
print(f"Claribel total items found: {len(all_ids)}")
ids_list=list(all_ids)
for i in range(0,len(ids_list),20):
    batch=",".join(ids_list[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status,catalog_product_id,catalog_listing"},timeout=30).json()
    for x in mg:
        if x.get("code")==200:
            b=x["body"]
            cp=b.get("catalog_product_id")
            if cp:
                # prefer ACTIVE over PAUSED over others
                cur=existing.get(cp)
                ranks={"active":3,"paused":2,"under_review":1,"closed":0,"inactive":0}
                if not cur or ranks.get(b.get("status"),0)>ranks.get(cur[1],0):
                    existing[cp]=(b["id"],b.get("status"))
print(f"Claribel CPID coverage: {len(existing)}")

# Plan: per (SKU,CPID): if exists active or paused -> reactivate+set sku; if closed -> new listing; if missing -> new listing
results={"published":[],"reactivated":[],"sku_set":[],"failed":[]}
total_targets=sum(len(c) for _,_,c in SKUS)
print(f"\n=== TARGETS: {total_targets} listings ===\n")

idx=0
for sku,name,cpids in SKUS:
    for cpid in cpids:
        idx+=1
        prefix=f"[{idx}/{total_targets}] {sku} {name} {cpid}"
        if cpid in existing:
            iid,st=existing[cpid]
            if st in ("active","paused","under_review"):
                # set SELLER_SKU + reactivate if needed
                pay={"attributes":[{"id":"SELLER_SKU","value_name":sku}]}
                r=requests.put(f"{API}/items/{iid}",headers=HJ,json=pay,timeout=30)
                if st!="active":
                    r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=30)
                    if r2.status_code in (200,201):
                        results["reactivated"].append((sku,cpid,iid))
                        print(f"  {prefix} -> REACTIVATED {iid}")
                    else:
                        results["failed"].append((sku,cpid,iid,f"reactivate {r2.status_code} {r2.text[:80]}"))
                        print(f"  {prefix} -> ERR reactivate {r2.status_code}")
                else:
                    results["sku_set"].append((sku,cpid,iid))
                    print(f"  {prefix} -> SKU_SET {iid} (already active)")
                time.sleep(0.5)
                continue
        # Get buy-box price
        pr=requests.get(f"{API}/products/{cpid}",headers=H,timeout=20).json()
        title=(pr.get("name") or "")[:60]
        # category from offers
        off=requests.get(f"{API}/products/{cpid}/items",headers=H,timeout=20).json()
        price=None; cat=None
        for o in (off.get("results") or [])[:1]:
            price=o.get("price")
            iid_o=o.get("item_id")
            if iid_o:
                tmp=requests.get(f"{API}/items/{iid_o}",headers=H,params={"attributes":"category_id,price"},timeout=15).json()
                cat=tmp.get("category_id")
                if not price: price=tmp.get("price")
        if not cat:
            cat=pr.get("category_id") or pr.get("domain_id")
        if not price:
            price=499
        if not cat:
            results["failed"].append((sku,cpid,None,"no_category"))
            print(f"  {prefix} -> SKIP no_category")
            continue
        payload={
            "site_id":"MLM","title":title,"category_id":cat,
            "price":price,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now",
            "listing_type_id":"gold_pro","condition":"new",
            "catalog_product_id":cpid,"catalog_listing":True,
            "shipping":{"mode":"me2","free_shipping":True},
            "attributes":[{"id":"SELLER_SKU","value_name":sku}]
        }
        r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
        if r.status_code in (200,201):
            d=r.json()
            results["published"].append((sku,cpid,d["id"],d.get("status"),d.get("price")))
            print(f"  {prefix} -> PUBLISHED {d['id']} ${d.get('price')} ({d.get('status')})")
        else:
            results["failed"].append((sku,cpid,None,f"{r.status_code} {r.text[:200]}"))
            print(f"  {prefix} -> FAIL {r.status_code} {r.text[:200]}")
        time.sleep(1.2)

print(f"\n=== RESUMEN ===")
print(f"  published:   {len(results['published'])}")
print(f"  reactivated: {len(results['reactivated'])}")
print(f"  sku_set:     {len(results['sku_set'])}")
print(f"  failed:      {len(results['failed'])}")
print("\n--- FAILED detail ---")
for sku,cp,iid,err in results["failed"]:
    print(f"  {sku} {cp} -> {err[:200]}")
