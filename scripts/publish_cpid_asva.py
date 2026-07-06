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

# 1. Get catalog product info
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
print(f"\n=== CATALOG {CPID} ===",flush=True)
print(f"  name: {p.get('name','?')}",flush=True)
print(f"  domain: {p.get('domain_id','?')}",flush=True)
print(f"  status: {p.get('status','?')}",flush=True)
print(f"  buy_box winner: {p.get('buy_box_winner',{}).get('price','?')}",flush=True)
print(f"  main_features: {[f.get('text','')[:60] for f in p.get('main_features',[])[:5]]}",flush=True)
attrs=p.get("attributes",[])
print(f"  attrs preview:",flush=True)
for a in attrs[:15]:
    print(f"    {a.get('id')}: {a.get('value_name','?')}",flush=True)

# 2. Category
cat_id=None
for a in attrs:
    if a.get("id")=="ITEM_CATEGORY":
        cat_id=a.get("value_id"); break
# Fallback: use product's domain
if not cat_id:
    dom=p.get("domain_id")
    print(f"  no ITEM_CATEGORY attr, will use children_ids/settings",flush=True)
    settings=p.get("settings",{})
    print(f"  settings: {json.dumps(settings)[:400]}",flush=True)

# Try the recommended way: use CPID in payload, MELI infers category
if not cat_id:
    # Get category by searching
    parents=p.get("parent_id")
    print(f"  parent_id: {parents}",flush=True)
    # Just try posting without category_id (CPID should suffice)

# 3. Get current buy_box price for reference
bbw_price=p.get("buy_box_winner",{}).get("price") or 0
# We'll price at 20% above lowest (or user can override); default match lowest
suggested_price = int(bbw_price) if bbw_price else 999
print(f"  suggested price: ${suggested_price}",flush=True)

# 4. Build minimal catalog payload
# For CPID publishing on MELI: send catalog_product_id, category_id, price, qty, currency, listing_type
# Category can often be derived if we send catalog_product_id + category_id from product settings
if not cat_id:
    # Try to get from a recent listing of this CPID
    search=requests.get(f"https://api.mercadolibre.com/products/{CPID}/items",headers=H,timeout=10).json()
    items_ex=search.get("results",[]) or []
    if items_ex:
        sample=items_ex[0]
        # Fetch sample to get category
        s2=requests.get(f"https://api.mercadolibre.com/items/{sample.get('item_id')}",headers=H,timeout=10).json()
        cat_id=s2.get("category_id")
        print(f"  cat_id from sample: {cat_id}",flush=True)

payload={
    "catalog_product_id":CPID,
    "category_id":cat_id,
    "price":suggested_price,
    "currency_id":"MXN",
    "available_quantity":QTY,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_pro",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                  {"id":"WARRANTY_TIME","value_name":"30 días"}]
}
print(f"\n=== POSTING ===\n{json.dumps(payload,indent=2)}",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id}",flush=True)
    print(f"  status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:1500]}",flush=True)
