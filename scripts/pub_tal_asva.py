import os, requests, time, json
API="https://api.mercadolibre.com"

tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]; print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
print(f"seller={UID}")

TARGETS=[
 "MLM70245995","MLM70245790","MLM70246385","MLM70246250","MLM70246080",
 "MLM52129383","MLM52129273","MLM52113823",
 "MLM70112010","MLM70063829","MLM70063831","MLM70063753","MLM70064197",
 "MLM70063779","MLM70063764","MLM70063872","MLM70063777",
 "MLM69963991","MLM69794800","MLM69794759","MLM69794771","MLM69794753",
 "MLM69794803","MLM69795006","MLM69794809","MLM69794978","MLM69794761",
 "MLM69795042","MLM69795023","MLM69795002",
 "MLM62726263","MLM62653473","MLM62651426","MLM62628964","MLM62627264",
 "MLM62626864","MLM62626851","MLM62626610","MLM62626475","MLM62626235",
 "MLM62594473","MLM62591134","MLM62570128","MLM62569211","MLM62555451",
 "MLM62550639"
]

# Pull ALL ASVA listings (active+paused+under_review) live and map by CPID
existing_cpids={}
sample_category=None
for st in ("active","paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        if not res: break
        for i in range(0,len(res),20):
            batch=",".join(res[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,catalog_product_id,title,category_id,price"},timeout=20).json()
            for x in mg:
                if x.get("code")!=200: continue
                b=x["body"]
                cp=b.get("catalog_product_id")
                if cp:
                    existing_cpids[cp]={"item_id":b["id"],"title":(b.get("title") or "")[:50],"cat":b.get("category_id")}
                    if not sample_category and "alchemia" in (b.get("title") or "").lower():
                        sample_category=b.get("category_id")
        if len(res)<50 or off>1500: break
        off+=50
print(f"\nexisting CPIDs in ASVA: {len(existing_cpids)}")
print(f"perfumes sample category: {sample_category}")

# Diff
to_publish=[c for c in TARGETS if c not in existing_cpids]
skipped=[(c,existing_cpids[c]) for c in TARGETS if c in existing_cpids]
print(f"\nto_publish: {len(to_publish)}")
print(f"skipped (already in ASVA): {len(skipped)}")
for c,info in skipped:
    print(f"  SKIP {c} (already as {info['item_id']}: {info['title']})")

# Default category for perfumes
DEFAULT_PERFUME_CAT=sample_category or "MLM177562"  # MLM177562 = Perfumes y Fragancias
PRICE=798
print(f"\nDEFAULT category for new publishes: {DEFAULT_PERFUME_CAT}")
print(f"DEFAULT price: ${PRICE}")

ok=[]; fail=[]
for i,cpid in enumerate(to_publish,1):
    try:
        pr=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
        title=(pr.get("name") or "")[:60]
        # Try category from offers, fallback to default
        cat=DEFAULT_PERFUME_CAT
        off=requests.get(f"{API}/products/{cpid}/items?limit=3",headers=H,timeout=10).json()
        if off.get("results"):
            for o in off["results"][:3]:
                it=o.get("item_id")
                if it:
                    tmp=requests.get(f"{API}/items/{it}",headers=H,params={"attributes":"category_id"},timeout=10).json()
                    if tmp.get("category_id"):
                        cat=tmp.get("category_id"); break
        payload={
            "site_id":"MLM","category_id":cat,
            "price":PRICE,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now",
            "listing_type_id":"gold_pro","condition":"new",
            "catalog_product_id":cpid,"catalog_listing":True,
            "shipping":{"mode":"me2","free_shipping":True}
        }
        r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
        if r.status_code in (200,201):
            d=r.json()
            ok.append((cpid,d["id"],d.get("status"),title[:40]))
            print(f"[{i:2}/{len(to_publish)}] PUB {cpid} -> {d['id']} {d.get('status')} '{title[:50]}'")
        else:
            fail.append((cpid,r.status_code,r.text[:200]))
            print(f"[{i:2}/{len(to_publish)}] FAIL {cpid} {r.status_code} {r.text[:200]}")
    except Exception as e:
        fail.append((cpid,0,str(e)[:100]))
        print(f"[{i:2}/{len(to_publish)}] EXC {cpid} {e}")
    time.sleep(1.0)

print(f"\n=== RESUMEN ===")
print(f"  targets={len(TARGETS)} skipped={len(skipped)} to_publish={len(to_publish)} ok={len(ok)} fail={len(fail)}")
print(f"\n--- FAIL detail ---")
for c,sc,t in fail: print(f"  {c} [{sc}] {t[:200]}")
