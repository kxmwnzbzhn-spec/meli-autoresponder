"""Resolver item_id → catalog_product_id y publicar en AH."""
import os, requests, time
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

# Pull AH existing CPIDs
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

# Resolve each: read item → get CPID → publish
ITEMS=["MLM5414275576","MLM2912468467"]
for iid in ITEMS:
    print(f"\n=== resolve {iid} ===")
    src=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    cpid=src.get("catalog_product_id")
    title=(src.get("title") or "")[:60]
    print(f"  title={title}")
    print(f"  cpid={cpid}")
    if not cpid:
        print(f"  ✗ no catalog_product_id on this item — skip")
        continue
    if cpid in own_cpids:
        print(f"  ⚠ AH already has cpid {cpid} — skip")
        continue
    base={"site_id":"MLM","category_id":"MLM1271","price":999,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    r=requests.post(f"{API}/items",headers=HJ,json=base,timeout=40)
    if r.status_code not in (200,201):
        r=requests.post(f"{API}/items",headers=HJ,json={**base,"title":title},timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        print(f"  ✓ PUBLISHED: {d['id']} status={d.get('status')} ${d.get('price')}")
        print(f"    url={d.get('permalink')}")
        own_cpids.add(cpid)
    else:
        print(f"  ✗ FAIL {r.status_code}: {r.text[:400]}")
    time.sleep(1.0)
