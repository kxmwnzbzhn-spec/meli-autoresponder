import os, requests, time, json
API="https://api.mercadolibre.com"
def tok(rt):
    return requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20).json()

tc=tok(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]); TC=tc["access_token"]
print(f"NEW_RT_CLARIBEL={tc.get('refresh_token')}")
HC={"Authorization":f"Bearer {TC}"}; HJC={**HC,"Content-Type":"application/json"}

# 1) Pause both items in Claribel
SKUS_FOUND={}
for sid in ["MLM5241631618","MLM2967278997"]:
    g=requests.get(f"{API}/items/{sid}",headers=HC,timeout=20).json()
    sku=None
    for a in (g.get("attributes") or []):
        if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
    cpid=g.get("catalog_product_id")
    SKUS_FOUND[sid]=(sku,cpid)
    print(f"\n=== {sid} BEFORE: status={g.get('status')} sku={sku} cpid={cpid} price={g.get('price')} qty={g.get('available_quantity')} ===")
    r=requests.put(f"{API}/items/{sid}",headers=HJC,json={"status":"paused","available_quantity":0},timeout=30)
    print(f"  pause+qty0: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
    g2=requests.get(f"{API}/items/{sid}",headers=HC,timeout=20).json()
    print(f"  AFTER: status={g2.get('status')} qty={g2.get('available_quantity')}")
    time.sleep(0.5)

# 2) Publish MLM63973616 in Claribel
NEW_CPID="MLM63973616"
print(f"\n\n=== PUBLISH {NEW_CPID} in Claribel ===")
# Try to get a source item from buy-box / offers
off=requests.get(f"{API}/products/{NEW_CPID}/items",headers=HC,timeout=20).json()
src_iid=None; src_cat=None; src_title=None
if off.get("results"):
    for o in off["results"][:3]:
        src_iid=o.get("item_id")
        if src_iid:
            tmp=requests.get(f"{API}/items/{src_iid}",headers=HC,params={"attributes":"id,title,category_id,price"},timeout=15).json()
            if tmp.get("category_id"):
                src_cat=tmp.get("category_id"); src_title=tmp.get("title"); break
print(f"source: iid={src_iid} cat={src_cat} title={(src_title or '')[:60]}")

# Fallback: read /products/{cpid} for the name + try domain
if not src_cat:
    pr=requests.get(f"{API}/products/{NEW_CPID}",headers=HC,timeout=20).json()
    print(f"  fallback /products: name={pr.get('name')} domain={pr.get('domain_id')} category_id={pr.get('category_id')}")

if not src_cat:
    print("  NO CATEGORY -> abort publish")
else:
    title=(src_title or pr.get("name") or "")[:60]
    payload={
        "site_id":"MLM","title":title,"category_id":src_cat,
        "price":449,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now",
        "listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":NEW_CPID,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}
    }
    r=requests.post(f"{API}/items",headers=HJC,json=payload,timeout=40)
    print(f"  POST: {r.status_code}")
    if r.status_code in (200,201):
        d=r.json()
        print(f"  NEW ITEM: {d['id']} status={d.get('status')} price=${d.get('price')} title='{(d.get('title') or '')[:70]}'")
        print(f"  URL: {d.get('permalink')}")
    else:
        print(f"  FAIL: {r.text[:600]}")
