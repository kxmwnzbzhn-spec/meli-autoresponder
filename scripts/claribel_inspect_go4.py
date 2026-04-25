import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_CLARIBEL","")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

# 1) Inspect MLM5244431296
print("=== MLM5244431296 ===")
g = requests.get("https://api.mercadolibre.com/items/MLM5244431296", headers=H).json()
print(f"  title: {g.get('title','?')}")
print(f"  status: {g.get('status')}")
print(f"  cond: {g.get('condition')}")
print(f"  price: ${g.get('price')}")
print(f"  cat: {g.get('category_id')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  catalog_listing: {g.get('catalog_listing')}")

# 2) Search for Go 4 Aqua catalog
print("\n=== Search Go 4 Aqua catalog ===")
r2 = requests.get("https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q=JBL+Go+4+Aqua&limit=10", headers=H).json()
for p in (r2.get("results") or [])[:8]:
    name = p.get("name","")[:70]
    pid = p.get("id")
    print(f"  {pid}: '{name}' status={p.get('status')}")

# Also search "JBL Go 4 mint" or similar
print("\n=== Search JBL Go 4 (general) ===")
r3 = requests.get("https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q=JBL+Go+4&limit=20", headers=H).json()
for p in (r3.get("results") or [])[:20]:
    name = p.get("name","")
    pid = p.get("id")
    if "aqua" in name.lower() or "agua" in name.lower() or "mint" in name.lower() or "celeste" in name.lower() or "verde" in name.lower():
        print(f"  ★ {pid}: '{name}'")
    else:
        print(f"    {pid}: '{name[:60]}'")
