import os, requests, json, sys

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM52113823"

# Product info
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
print(f"\n=== CATALOG {CPID} ===",flush=True)
print(f"  name: {p.get('name','?')}",flush=True)
print(f"  domain: {p.get('domain_id','?')}",flush=True)
print(f"  status: {p.get('status','?')}",flush=True)
bbw=p.get("buy_box_winner") or {}
print(f"  buy_box winner price: ${bbw.get('price','?')}",flush=True)

# Get category from CPID attrs or from similar existing item
cat_id=None
for a in p.get("attributes",[]):
    if a.get("id")=="ITEM_CATEGORY":
        cat_id=a.get("value_id"); break
print(f"  cat from CPID: {cat_id}",flush=True)

# Fallback: use REF Alchemia category MLM1271
if not cat_id:
    dom=p.get("domain_id","")
    if "PERFUME" in dom.upper() or "ESOTERIC" in dom.upper():
        cat_id="MLM1271"
    else:
        cat_id="MLM1271"  # default perfumes for now
    print(f"  cat fallback: {cat_id}",flush=True)

suggested=int(bbw.get("price") or 399)
QTY=1  # default 1 — user didn't specify inventory this time

# Try catalog_listing pattern
payload={
    "catalog_product_id":CPID,
    "category_id":cat_id,
    "price":suggested,
    "currency_id":"MXN",
    "available_quantity":QTY,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_pro",
    "catalog_listing":True,
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                  {"id":"WARRANTY_TIME","value_name":"30 días"}]
}
print(f"\n=== POSTING === price=${suggested} qty={QTY} cat={cat_id}",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id}",flush=True)
    print(f"  status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:2000]}",flush=True)
