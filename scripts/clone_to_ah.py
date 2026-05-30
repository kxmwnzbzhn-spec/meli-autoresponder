import os, requests, time, json
API="https://api.mercadolibre.com"

def tok(rt):
    return requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20).json()

# Read source via any account token (read works cross-account for public items)
ta=tok(os.environ["MELI_REFRESH_TOKEN_AH"])
TA=ta["access_token"]
print(f"NEW_RT_AH={ta.get('refresh_token')}")
HA={"Authorization":f"Bearer {TA}"}; HJA={**HA,"Content-Type":"application/json"}

SRC="MLM5400882616"
src=requests.get(f"{API}/items/{SRC}",headers=HA,timeout=20).json()
if src.get("error"):
    print(f"ERR reading source: {src}")
    raise SystemExit(1)
print(f"\n=== SOURCE {SRC} ===")
print(f"seller_id={src.get('seller_id')}")
print(f"title={(src.get('title') or '')[:80]}")
print(f"price=${src.get('price')} qty={src.get('available_quantity')}")
print(f"category_id={src.get('category_id')}")
print(f"catalog_product_id={src.get('catalog_product_id')} catalog_listing={src.get('catalog_listing')}")
print(f"inventory_id={src.get('inventory_id')}")
print(f"sub_status={src.get('sub_status')}")

# AH user
me=requests.get(f"{API}/users/me",headers=HA,timeout=10).json()
UID=me["id"]
print(f"\nTarget account AH seller={UID} nick={me.get('nickname')}")

# Build payload — if catalog_listing, use catalog approach
cpid=src.get("catalog_product_id")
cat=src.get("category_id")
title=(src.get("title") or "")[:60]
price=src.get("price") or 999

if cpid and src.get("catalog_listing"):
    print(f"\n→ Cloning as CATALOG listing")
    # Check if AH already has this CPID
    own_search=requests.get(f"{API}/users/{UID}/items/search?status=active&limit=50",headers=HA,timeout=15).json()
    own_ids=own_search.get("results") or []
    own_cpids=set()
    for i in range(0,len(own_ids),20):
        batch=",".join(own_ids[i:i+20])
        mg=requests.get(f"{API}/items",headers=HA,params={"ids":batch,"attributes":"catalog_product_id"},timeout=20).json()
        for x in mg:
            if x.get("code")==200:
                cp=(x["body"] or {}).get("catalog_product_id")
                if cp: own_cpids.add(cp)
    if cpid in own_cpids:
        print(f"AH already has {cpid} — skipping clone")
        raise SystemExit(0)
    base={"site_id":"MLM","category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    r=requests.post(f"{API}/items",headers=HJA,json=base,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        print(f"✓ CLONED (no title) -> {d['id']} {d.get('status')} ${d.get('price')}")
        print(f"URL: {d.get('permalink')}")
    elif r.status_code==400 and "required_fields" in r.text:
        # retry with title
        r2=requests.post(f"{API}/items",headers=HJA,json={**base,"title":title},timeout=40)
        if r2.status_code in (200,201):
            d=r2.json()
            print(f"✓ CLONED (with title) -> {d['id']} {d.get('status')} ${d.get('price')}")
            print(f"URL: {d.get('permalink')}")
        else:
            print(f"✗ FAIL with title: {r2.status_code} {r2.text[:400]}")
    else:
        print(f"✗ FAIL: {r.status_code} {r.text[:400]}")
else:
    print(f"\n→ Cloning as TRADITIONAL (non-catalog)")
    pictures=[{"source":p["secure_url"]} for p in (src.get("pictures") or [])][:10]
    attrs=[]
    for a in (src.get("attributes") or []):
        aid=a.get("id")
        if aid in ("SELLER_SKU","IS_GAMER","DETAILED_MODEL"): continue
        if not (a.get("value_name") or a.get("value_id")): continue
        o={"id":aid}
        if a.get("value_id"): o["value_id"]=a["value_id"]
        if a.get("value_name"): o["value_name"]=a["value_name"]
        attrs.append(o)
    payload={
        "site_id":"MLM","title":title,"category_id":cat,
        "price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now",
        "listing_type_id":"gold_special","condition":"new",
        "description":{"plain_text":"Producto original. Sellado. Envío inmediato."},
        "pictures":pictures,
        "attributes":attrs,
        "shipping":{"mode":"me2","free_shipping":False}
    }
    r=requests.post(f"{API}/items",headers=HJA,json=payload,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        print(f"✓ CLONED -> {d['id']} {d.get('status')} ${d.get('price')}")
        print(f"URL: {d.get('permalink')}")
    else:
        print(f"✗ FAIL: {r.status_code} {r.text[:500]}")
