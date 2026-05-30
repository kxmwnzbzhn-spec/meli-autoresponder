"""Adrián batch 1 v2: try TODOS los candidatos por perfume hasta que uno publique."""
import os, requests, time, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]

# Existing CPIDs
existing_cpids=set()
for st in ("active","paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        for i in range(0,len(res),20):
            batch=",".join(res[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"catalog_product_id"},timeout=20).json()
            for x in mg:
                if x.get("code")==200:
                    cp=(x["body"] or {}).get("catalog_product_id")
                    if cp: existing_cpids.add(cp)
        if len(res)<50 or off>1500: break
        off+=50
print(f"Adrián existing CPIDs: {len(existing_cpids)}")

TARGETS=[
  {"q":"Armaf Club De Nuit Maleka","size":"105 ml"},
  {"q":"Emporio Armani Stronger With You","size":"100 ml"},
  {"q":"Initio Oud For Greatness","size":"90 ml"},
  {"q":"Armaf Lions Club Rugir","size":"100 ml"},
  {"q":"Al Haramain Amber Oud Ruby Edition","size":"100 ml"},
]

def find_candidates(query,target_size):
    r=requests.get(f"{API}/products/search",headers=H,params={"site_id":"MLM","q":query,"status":"active","limit":15},timeout=20).json()
    cands=[]
    for p in (r.get("results") or []):
        cpid=p.get("id"); name=(p.get("name") or "")
        lower=name.lower()
        if "200 ml" in lower or "200ml" in lower: continue
        sc=0
        if target_size.replace(" ","") in lower.replace(" ",""): sc+=10
        # Prefer NEWER CPIDs (higher number) — often have valid categories
        try: cpid_num=int(cpid.replace("MLM",""))
        except: cpid_num=0
        cands.append((sc,cpid_num,cpid,name))
    cands.sort(key=lambda x:(-x[0],-x[1]))
    return cands

def try_publish(cpid,name):
    """Try to publish. Returns (success, response/error, payload_used)."""
    pr=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
    bb=pr.get("buy_box_winner") or {}
    price=bb.get("price") or 999
    cat=None
    if bb.get("item_id"):
        tmp=requests.get(f"{API}/items/{bb['item_id']}",headers=H,params={"attributes":"category_id"},timeout=10).json()
        cat=tmp.get("category_id")
    if not cat:
        cat="MLM177562"
    base={"site_id":"MLM","category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    # Try without title
    r=requests.post(f"{API}/items",headers=HJ,json=base,timeout=30)
    if r.status_code in (200,201): return True, r.json(), "no_title"
    # Retry with title
    r2=requests.post(f"{API}/items",headers=HJ,json={**base,"title":name[:60]},timeout=30)
    if r2.status_code in (200,201): return True, r2.json(), "with_title"
    return False, {"no_title":r.text[:200],"with_title":r2.text[:200]}, "both_failed"

results={"ok":[],"skip":[],"fail":[]}
for t in TARGETS:
    print(f"\n=== {t['q']} target={t['size']} ===")
    cands=find_candidates(t["q"],t["size"])
    available=[c for c in cands if c[2] not in existing_cpids]
    if not available:
        print(f"  NO candidates (or all already in Adrián)")
        results["skip"].append((t["q"],"no_candidates_or_all_dup"))
        continue
    print(f"  candidates: {len(available)}")
    for sc,n,cp,name in available[:5]:
        print(f"    sc={sc} {cp} | {name[:75]}")
    # Try each in order
    success=False
    for sc,n,cp,name in available[:5]:
        print(f"  → trying {cp}...")
        ok,resp,how=try_publish(cp,name)
        if ok:
            print(f"  ✓ PUBLISHED via {how}: {resp['id']} status={resp.get('status')} ${resp.get('price')}")
            results["ok"].append((t["q"],cp,resp["id"],resp.get("status"),resp.get("price"),name,how))
            existing_cpids.add(cp)
            success=True
            break
        else:
            print(f"  ✗ {cp} both failed: {json.dumps(resp)[:300]}")
        time.sleep(1)
    if not success:
        results["fail"].append((t["q"],[c[2] for c in available[:5]]))
    time.sleep(1)

print(f"\n\n=== RESUMEN === ok={len(results['ok'])} skip={len(results['skip'])} fail={len(results['fail'])}")
print("\n=== LINKS publicados ===")
for q,cpid,iid,st,pr,name,how in results["ok"]:
    print(f"\n• {q}")
    print(f"  CPID catálogo: {cpid}")
    print(f"  Nuevo listing: {iid} ({st}) ${pr}")
    print(f"  Producto: {name[:80]}")
    print(f"  Via: {how}")
print("\n=== FAIL detail ===")
for q,cps in results["fail"]:
    print(f"  {q} → tried {len(cps)} CPIDs all failed: {cps}")
