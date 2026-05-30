"""Buscar catálogo MELI por EAN, publicar todos los CPIDs en Adrián.
Recipe validado: category=MLM1271, gold_pro, title fallback, price=999."""
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
print(f"seller={UID} nick={me.get('nickname')}")

# Pull existing CPIDs
own_cpids=set()
for st in ("active","paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        for i in range(0,len(res),20):
            batch=",".join(res[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,catalog_product_id"},timeout=20).json()
            for x in mg:
                if x.get("code")==200:
                    cp=(x["body"] or {}).get("catalog_product_id")
                    if cp: own_cpids.add(cp)
        if len(res)<50 or off>1000: break
        off+=50
print(f"AH existing CPIDs: {len(own_cpids)}")

EANS=[
"3348900103870","3348901362832","3348900417878","3348901727297","3348901368247",
"3348901640916","3348901728836","8054754401059","3423473020516","8054754400113",
"3349668630349","3349669630264","3349669579839","3349668617050","3614273604932",
"3614272907690","3614274222067","3614247150926","3614274219579","3614274184631",
"3614274040067","3614270561634","888066000079","888066151993","3616302022472",
"3432240506641","3700559605905","3700559623855","3701415900080","3700550218227",
"6291100131716","6291100130498","6291106814910","6291100133444","6291100130375",
"6291106811568","6291106811513","8435415076944","8435415091251","8435415032315",
"60894058220","3760060761279","3760060761880","6293365212230","811901023018",
"701666411055","3346470148321","3346470148345"
]
print(f"Total EANs: {len(EANS)}")

def search_by_ean(ean):
    """Try multiple endpoints to find catalog products by EAN."""
    cpids=[]
    # Try /products/search with q param (returns products matching query)
    try:
        r=requests.get(f"{API}/products/search",headers=H,params={"site_id":"MLM","q":ean,"status":"active","limit":5},timeout=15).json()
        for p in (r.get("results") or []):
            cp=p.get("id")
            if cp and cp not in cpids:
                cpids.append((cp,p.get("name","")))
    except: pass
    # Try /sites/MLM/search with GTIN filter
    try:
        r=requests.get(f"{API}/sites/MLM/search",headers=H,params={"q":ean,"limit":5},timeout=15).json()
        for it in (r.get("results") or []):
            cp=it.get("catalog_product_id")
            if cp and cp not in [c[0] for c in cpids]:
                cpids.append((cp,it.get("title","")))
    except: pass
    return cpids

def publish_cpid(cpid,name):
    """Try publish; with-title fallback. Returns (ok, new_item_id_or_err)."""
    base={"site_id":"MLM","category_id":"MLM1271","price":999,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    r=requests.post(f"{API}/items",headers=HJ,json=base,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        return True, d
    # Retry with title
    r2=requests.post(f"{API}/items",headers=HJ,json={**base,"title":name[:60]},timeout=40)
    if r2.status_code in (200,201):
        d=r2.json()
        return True, d
    return False, {"no_title_code":r.status_code,"no_title_err":r.text[:200],"with_title_code":r2.status_code,"with_title_err":r2.text[:200]}

published=[]; skipped=[]; not_found=[]; failed=[]
for idx,ean in enumerate(EANS,1):
    print(f"\n[{idx}/{len(EANS)}] EAN {ean}")
    cands=search_by_ean(ean)
    if not cands:
        print(f"  NO catalog match found")
        not_found.append(ean)
        time.sleep(0.5)
        continue
    print(f"  found {len(cands)} candidates: {[c[0] for c in cands]}")
    # Try each candidate
    success=False
    for cpid,name in cands[:3]:
        if cpid in own_cpids:
            print(f"  ⚠ {cpid} already in AH, skip")
            skipped.append((ean,cpid,"already_in_AH"))
            success=True
            break
        ok,resp=publish_cpid(cpid,name)
        if ok:
            published.append((ean,cpid,resp["id"],resp.get("status"),resp.get("price"),name))
            own_cpids.add(cpid)
            print(f"  ✓ {cpid} → {resp['id']} {resp.get('status')} ${resp.get('price')} | {name[:60]}")
            success=True
            break
        else:
            print(f"  ✗ {cpid} failed: nt={resp['no_title_code']} t={resp['with_title_code']}")
    if not success:
        failed.append((ean,[c[0] for c in cands]))
    time.sleep(0.8)

print(f"\n\n=== RESUMEN ===")
print(f"  published: {len(published)}")
print(f"  skipped (already in AH): {len(skipped)}")
print(f"  not_found in catalog: {len(not_found)}")
print(f"  failed (catalog match but couldn't publish): {len(failed)}")

print("\n=== PUBLISHED ===")
for ean,cp,iid,st,pr,name in published:
    print(f"  EAN {ean} cpid={cp} → {iid} {st} ${pr} | {name[:60]}")
print("\n=== NOT FOUND in catalog ===")
for ean in not_found: print(f"  {ean}")
print("\n=== FAILED ===")
for ean,cps in failed: print(f"  EAN {ean} cpids tried: {cps}")
