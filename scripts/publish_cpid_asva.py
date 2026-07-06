import os, requests, json, sys

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM74984237"
QTY=200

# Reference: get an existing ASVA alchemia to steal category + attributes shape
REF="MLM3042017797"
ref=requests.get(f"https://api.mercadolibre.com/items/{REF}",headers=H,timeout=10).json()
cat_id=ref.get("category_id")
ref_price=ref.get("price")
print(f"REF {REF}: cat={cat_id} price=${ref_price} title={ref.get('title','?')[:60]}",flush=True)

# Product info
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
print(f"\nCPID {CPID}: {p.get('name','?')[:80]}",flush=True)
print(f"  domain: {p.get('domain_id')}",flush=True)
bbw=p.get("buy_box_winner") or {}
suggested=int(bbw.get("price") or ref_price or 399)
print(f"  buy_box: ${bbw.get('price','?')}  suggested: ${suggested}",flush=True)

# Category from product if available
prod_cat=None
for a in p.get("attributes",[]):
    if a.get("id")=="ITEM_CATEGORY":
        prod_cat=a.get("value_id"); break
if prod_cat:
    cat_id=prod_cat
    print(f"  cat from CPID attrs: {prod_cat}",flush=True)
print(f"  using category: {cat_id}",flush=True)

# Build payload — use catalog_listing pattern
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
print(f"\n=== POSTING === payload:\n{json.dumps(payload,indent=2)}",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:2000]}",flush=True)
