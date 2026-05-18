import os, requests, json
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token","client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}
# Catalog product hub
print("=== Catalog product MLM45742213 ===")
prod = requests.get("https://api.mercadolibre.com/products/MLM45742213", headers=h, timeout=20).json()
print("name:", prod.get("name"))
# Get items the seller has under this product
print("=== Seller's items for this product ===")
search = requests.get("https://api.mercadolibre.com/sites/MLM/search",
    params={"seller_id": 1668713481, "product_id": "MLM45742213"},
    headers=h, timeout=20).json()
for r in search.get("results", [])[:10]:
    print(f"item: {r.get('id')} | {r.get('title','')[:80]}")
    print(f"  price: ${r.get('price')} | qty: {r.get('available_quantity')} | sold: {r.get('sold_quantity')} | status: {r.get('status')}")
    print(f"  link: {r.get('permalink')}")
    attrs = {a.get('id'): a.get('value_name') for a in r.get('attributes',[])}
    print(f"  color: {attrs.get('COLOR')}")
    print(f"  thumb: {r.get('thumbnail','')}")
print("=== Direct item MLM3545177574 (rosa) ===")
item = requests.get("https://api.mercadolibre.com/items/MLM3545177574", headers=h, timeout=20).json()
print("title:", item.get("title"))
print("price:", item.get("price"))
print("qty:", item.get("available_quantity"))
print("perma:", item.get("permalink"))
print("shipping:", (item.get("shipping") or {}).get("logistic_type"), "free:", (item.get("shipping") or {}).get("free_shipping"))
print("=== Top 4 pics rosa ===")
for i,p in enumerate(item.get("pictures",[])[:4]):
    print(f"  pic{i}: {p.get('secure_url')}")
