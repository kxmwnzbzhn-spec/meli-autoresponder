import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPIDS=["MLM75427909","MLM75427910"]
results=[]

for CPID in CPIDS:
    print(f"\n=== CPID {CPID} ===",flush=True)
    p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
    name=p.get("name","?")
    dom=p.get("domain_id","?")
    print(f"  name: {name[:100]}",flush=True)
    print(f"  domain: {dom}",flush=True)
    bbw=p.get("buy_box_winner") or {}
    print(f"  buy_box: ${bbw.get('price','?')}",flush=True)
    
    cat_id=None
    for a in p.get("attributes",[]):
        if a.get("id")=="ITEM_CATEGORY":
            cat_id=a.get("value_id"); break
    if not cat_id: cat_id="MLM1271"
    print(f"  cat: {cat_id}",flush=True)
    
    price=int(bbw.get("price") or 399)
    payload={
        "catalog_product_id":CPID,
        "category_id":cat_id,
        "price":price,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "condition":"new",
        "listing_type_id":"gold_pro",
        "catalog_listing":True,
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                      {"id":"WARRANTY_TIME","value_name":"30 días"}]
    }
    post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
    if "id" in post:
        new_id=post["id"]
        print(f"  ✅ POSTED: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
        print(f"  title: {post.get('title','?')[:80]}",flush=True)
        print(f"  URL: {post.get('permalink','?')}",flush=True)
        results.append((CPID, new_id, post.get('title','?')[:80], price))
    else:
        print(f"  ❌ FAIL: {json.dumps(post)[:800]}",flush=True)
        results.append((CPID, None, None, None))

print("\n=== SUMMARY ===",flush=True)
for cpid, new_id, title, price in results:
    print(f"  {cpid} -> {new_id} ${price} {title}",flush=True)
