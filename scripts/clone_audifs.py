import os, requests, time
API="https://api.mercadolibre.com"

def tok(rt):
    return requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":rt},timeout=20).json()

# ASVA token (read source)
ta=tok(os.environ["MELI_REFRESH_TOKEN_ASVA"])
TA=ta["access_token"]
print(f"NEW_RT_ASVA={ta.get('refresh_token')}")
HA={"Authorization":f"Bearer {TA}"}
me_a=requests.get(f"{API}/users/me",headers=HA,timeout=15).json()
UIDA=me_a["id"]; print(f"ASVA seller={UIDA} nick={me_a.get('nickname')}")

# MAYRELY token (write target)
tm=tok(os.environ["MELI_REFRESH_TOKEN_MAYRELY"])
TM=tm["access_token"]
print(f"NEW_RT_MAYRELY={tm.get('refresh_token')}")
HM={"Authorization":f"Bearer {TM}"}; HJM={**HM,"Content-Type":"application/json"}
me_m=requests.get(f"{API}/users/me",headers=HM,timeout=15).json()
UIDM=me_m["id"]; print(f"MAYRELY seller={UIDM} nick={me_m.get('nickname')}")

# Find ASVA audífonos. Category root: MLM1051 (Electronica/Audio/Audifonos) or MLM1648 (Electronica). Let me search active items and filter by category path containing audifonos.
ids=[]; scroll=None
while True:
    p={"search_type":"scan","limit":100,"status":"active"}
    if scroll: p["scroll_id"]=scroll
    r=requests.get(f"{API}/users/{UIDA}/items/search",headers=HA,params=p,timeout=30).json()
    ids+=r.get("results",[])
    scroll=r.get("scroll_id")
    if not scroll or not r.get("results"): break
print(f"\nASVA active items: {len(ids)}")

# Get details + filter by audífonos via title or category
audifs=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"{API}/items",headers=HA,params={"ids":batch,"attributes":"id,title,price,category_id,available_quantity,sold_quantity,pictures,attributes,variations,listing_type_id,shipping,catalog_listing,catalog_product_id"},timeout=30).json()
    for x in r:
        if x.get("code")!=200: continue
        b=x["body"]
        t=(b.get("title") or "").lower()
        cat=b.get("category_id","")
        # audífonos / auriculares / headphones
        if any(k in t for k in ["audífono","audifono","audifonos","audifonos","audifono","auricular","headphone","earbud","in-ear","airdots","buds","tws"]):
            audifs.append(b)
        elif cat.startswith("MLM1000") or cat=="MLM1051":  # audio categories
            audifs.append(b)
print(f"audífonos detectados: {len(audifs)}")
for a in audifs[:30]:
    print(f"  {a['id']} sold={a.get('sold_quantity'):>3} ${a.get('price'):>5} cat={a.get('category_id')} cat_listing={a.get('catalog_listing')} cpid={a.get('catalog_product_id')} | {a.get('title','')[:80]}")

if not audifs:
    print("No se detectaron audífonos en ASVA")
    raise SystemExit(0)

# Pick TOP 1 by sold (test)
audifs.sort(key=lambda b:-(b.get("sold_quantity") or 0))
pick=audifs[0]
print(f"\n>>> PICK for test: {pick['id']} sold={pick.get('sold_quantity')} ${pick.get('price')} title='{pick.get('title')}'")

# Republish in MAYRELY as tradicional (catalog_listing=False) condition=new to avoid under_review on new account
title=(pick.get("title") or "")[:60]
cat=pick.get("category_id")
price=pick.get("price")
pictures=[{"source":p["secure_url"]} for p in (pick.get("pictures") or [])][:10]
attrs=[]
for a in (pick.get("attributes") or []):
    aid=a.get("id");
    if aid in ("SELLER_SKU","IS_GAMER"): continue
    if not a.get("value_name") and not a.get("value_id"): continue
    o={"id":aid}
    if a.get("value_id"): o["value_id"]=a["value_id"]
    if a.get("value_name"): o["value_name"]=a["value_name"]
    attrs.append(o)
payload={
    "site_id":"MLM",
    "title":title,
    "category_id":cat,
    "price":price,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_special",
    "condition":"new",
    "description":{"plain_text":"Producto 100% original. Sellado de fábrica. Envío inmediato."},
    "pictures":pictures,
    "attributes":attrs,
    "shipping":{"mode":"me2","free_shipping":False}
}
print(f"\nposting to MAYRELY...")
r=requests.post(f"{API}/items",headers=HJM,json=payload,timeout=40)
print(f"POST: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"NEW ITEM: {d['id']} status={d.get('status')} price={d.get('price')} title='{d.get('title')[:70]}'")
    print(f"URL: {d.get('permalink')}")
else:
    print(f"ERROR: {r.text[:600]}")
