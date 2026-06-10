"""Deep inspect MLM2969976211 to understand exactly what we're cloning."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_AH={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}

SRC="MLM2969976211"
g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"\n=== SRC item {SRC} ===")
print(f"title: {g.get('title')}")
print(f"category_id: {g.get('category_id')}")
print(f"status: {g.get('status')}")
print(f"price: {g.get('price')}")
print(f"available_quantity: {g.get('available_quantity')}")
print(f"listing_type_id: {g.get('listing_type_id')}")
print(f"catalog_product_id: {g.get('catalog_product_id')}")
print(f"family_name: {g.get('family_name')}")
print(f"condition: {g.get('condition')}")
print(f"pictures count: {len(g.get('pictures') or [])}")

print(f"\n--- attributes ---")
for a in (g.get("attributes") or []):
    aid=a.get("id"); vn=a.get("value_name"); vi=a.get("value_id")
    print(f"  {aid}: name='{vn}' id={vi}")

# Get category required attributes
cat=g.get("category_id")
print(f"\n=== Category {cat} required attrs ===")
ca=requests.get(f"{API}/categories/{cat}/attributes",headers=H,timeout=10).json()
for a in ca:
    tags=a.get("tags") or {}
    if tags.get("required") or tags.get("catalog_required") or a.get("id") in ("BRAND","PERFUME_NAME","UNIT_VOLUME","GENDER","ITEM_CONDITION","FRAGRANCE_TYPE","EAU_DE","GTIN","EMPTY_GTIN_REASON"):
        print(f"  {'★ REQ' if tags.get('required') else '   '} {a.get('id'):26s} {a.get('value_type'):14s} {a.get('name')}")

# Get description of source
print(f"\n=== SRC description ===")
dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
print((dd.get("plain_text") or "")[:1500])

# Print picture URLs
print(f"\n=== SRC pictures ===")
for p in (g.get("pictures") or [])[:8]:
    print(f"  {p.get('url')}")
