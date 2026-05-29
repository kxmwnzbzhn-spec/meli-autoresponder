import os, requests, time
API="https://api.mercadolibre.com"

def tok(rt):
    return requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":rt},timeout=20).json()

tc=tok(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"])
TC=tc["access_token"]; print(f"NEW_RT_CLARIBEL={tc.get('refresh_token')}")
HC={"Authorization":f"Bearer {TC}"}; HJC={**HC,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=HC,timeout=15).json()
UID=me["id"]

# Use ANY token (Wilbert/Yiriam) for reading source items
ty=tok(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]); TY=ty["access_token"]; print(f"NEW_RT_YC_NEW={ty.get('refresh_token')}")
HY={"Authorization":f"Bearer {TY}"}
tw=tok(os.environ["MELI_REFRESH_TOKEN_WILBERT"]); TW=tw["access_token"]; print(f"NEW_RT_WILBERT={tw.get('refresh_token')}")
HW={"Authorization":f"Bearer {TW}"}

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
 ("ELEC-031","JBL Clip 5 Aqua",[]),
 ("ELEC-021","Bose Soundlink Home Negro",["MLM49963786"]),
 ("ELEC-025","Bose Soundlink Home Silver",["MLM50131488"]),
 ("ELEC-014","Sony XB100 Negro",["MLM25912333"]),
]

def find_source(cpid):
    """Find any seller's listing for this CPID via offers API. Returns (item_id, title, category_id, price)."""
    # Try /products/{cpid}/items first (using any of our tokens)
    for H in [HW, HY, HC]:
        try:
            r=requests.get(f"{API}/products/{cpid}/items",headers=H,timeout=15)
            if r.status_code==200:
                data=r.json()
                results=data.get("results") or []
                if results:
                    # take first result; get item details
                    item_id=results[0].get("item_id")
                    if item_id:
                        det=requests.get(f"{API}/items/{item_id}",headers=H,params={"attributes":"id,title,price,category_id"},timeout=15).json()
                        return (item_id, det.get("title"), det.get("category_id"), det.get("price"))
        except: pass
    # Fallback: /sites/MLM/search?q=...
    return (None,None,None,None)

def discover_aqua_clip5():
    for H in [HW,HY,HC]:
        r=requests.get(f"{API}/sites/MLM/search",headers=H,params={"q":"JBL Clip 5 Aqua","category":"MLM5072","limit":20},timeout=20).json()
        for it in (r.get("results") or [])[:30]:
            t=(it.get("title") or "").lower()
            if "clip 5" in t and ("aqua" in t or "acqua" in t):
                cp=it.get("catalog_product_id")
                if cp:
                    return cp, it.get("id")
    return None, None

aqua_cp,aqua_iid=discover_aqua_clip5()
print(f"\nClip 5 Aqua: cpid={aqua_cp} from item={aqua_iid}")
if aqua_cp:
    new=[]
    for sku,name,cpids in SKUS:
        if sku=="ELEC-031": new.append((sku,name,[aqua_cp]))
        else: new.append((sku,name,cpids))
    SKUS=new

# Map Claribel existing CPID -> (item_id, status)
print("\nMapping Claribel existing listings...")
existing={}
for st in ["active","paused","under_review","programmed","closed","inactive"]:
    scroll=None
    while True:
        p={"search_type":"scan","limit":100,"status":st}
        if scroll: p["scroll_id"]=scroll
        r=requests.get(f"{API}/users/{UID}/items/search",headers=HC,params=p,timeout=30).json()
        ids=r.get("results",[])
        for i in range(0,len(ids),20):
            batch=",".join(ids[i:i+20])
            mg=requests.get(f"{API}/items",headers=HC,params={"ids":batch,"attributes":"id,status,catalog_product_id"},timeout=30).json()
            for x in mg:
                if x.get("code")==200:
                    b=x["body"]
                    cp=b.get("catalog_product_id")
                    if cp:
                        cur=existing.get(cp)
                        ranks={"active":3,"paused":2,"under_review":1,"closed":0,"inactive":0}
                        if not cur or ranks.get(b.get("status"),0)>ranks.get(cur[1],0):
                            existing[cp]=(b["id"],b.get("status"))
        scroll=r.get("scroll_id")
        if not scroll or not ids: break
print(f"Claribel current CPID coverage: {len(existing)}")

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
                pay={"attributes":[{"id":"SELLER_SKU","value_name":sku}]}
                requests.put(f"{API}/items/{iid}",headers=HJC,json=pay,timeout=30)
                if st!="active":
                    r2=requests.put(f"{API}/items/{iid}",headers=HJC,json={"status":"active"},timeout=30)
                    if r2.status_code in (200,201):
                        results["reactivated"].append((sku,cpid,iid))
                        print(f"  {prefix} -> REACTIVATED {iid}")
                    else:
                        results["failed"].append((sku,cpid,iid,f"reactivate {r2.status_code} {r2.text[:120]}"))
                        print(f"  {prefix} -> ERR reactivate {r2.status_code}")
                else:
                    results["sku_set"].append((sku,cpid,iid))
                    print(f"  {prefix} -> SKU_SET {iid}")
                time.sleep(0.4); continue
        src_iid,title,cat,price=find_source(cpid)
        if not cat:
            results["failed"].append((sku,cpid,None,"no_source_category"))
            print(f"  {prefix} -> SKIP no_source_category (src_iid={src_iid})")
            continue
        if not title: title=name
        if not price: price=499
        payload={
            "site_id":"MLM","title":title[:60],"category_id":cat,
            "price":price,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now",
            "listing_type_id":"gold_pro","condition":"new",
            "catalog_product_id":cpid,"catalog_listing":True,
            "shipping":{"mode":"me2","free_shipping":True},
            "attributes":[{"id":"SELLER_SKU","value_name":sku}]
        }
        r=requests.post(f"{API}/items",headers=HJC,json=payload,timeout=40)
        if r.status_code in (200,201):
            d=r.json()
            results["published"].append((sku,cpid,d["id"],d.get("status"),d.get("price")))
            print(f"  {prefix} -> PUB {d['id']} ${d.get('price')} ({d.get('status')})")
        else:
            results["failed"].append((sku,cpid,None,f"{r.status_code} {r.text[:300]}"))
            print(f"  {prefix} -> FAIL {r.status_code} {r.text[:250]}")
        time.sleep(1.2)

print(f"\n=== RESUMEN === pub={len(results['published'])} react={len(results['reactivated'])} sku_set={len(results['sku_set'])} fail={len(results['failed'])}")
print("\n--- FAIL detail ---")
for sku,cp,iid,err in results["failed"]:
    print(f"  {sku} {cp} -> {err[:250]}")
