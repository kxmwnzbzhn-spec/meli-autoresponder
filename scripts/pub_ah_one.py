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
print(f"seller={UID} nick={me.get('nickname')}")

CPID="MLM18209912"
# Check existing
own_ids=[]
off=0
while True:
    r=requests.get(f"{API}/users/{UID}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    own_ids.extend(res)
    if len(res)<50 or off>1000: break
    off+=50
for st in ("paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        own_ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50
already=False
for i in range(0,len(own_ids),20):
    batch=",".join(own_ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,catalog_product_id,status"},timeout=20).json()
    for x in mg:
        if x.get("code")==200 and (x["body"] or {}).get("catalog_product_id")==CPID:
            print(f"\n⚠ AH already has CPID {CPID}: item={x['body']['id']} status={x['body']['status']}")
            already=True

# Get product info for title
pr=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
title=(pr.get("name") or "")[:60]
print(f"\nproduct name: {pr.get('name')}")
print(f"title (truncated): {title}")

if not already:
    base={"site_id":"MLM","category_id":"MLM1271","price":999,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":CPID,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    # Try without title first
    r=requests.post(f"{API}/items",headers=HJ,json=base,timeout=40)
    print(f"\nTry 1 (no title): {r.status_code}")
    if r.status_code not in (200,201):
        # Retry with title
        r=requests.post(f"{API}/items",headers=HJ,json={**base,"title":title},timeout=40)
        print(f"Try 2 (with title): {r.status_code}")
    if r.status_code in (200,201):
        d=r.json()
        print(f"\n✓ PUBLISHED: {d['id']}")
        print(f"  status={d.get('status')} price=${d.get('price')}")
        print(f"  title={(d.get('title') or '')[:80]}")
        print(f"  url={d.get('permalink')}")
    else:
        print(f"\n✗ FAIL {r.status_code}: {r.text[:500]}")
else:
    print("Skipping publish (already exists)")
