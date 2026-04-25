import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL","")

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}

# Try with all tokens to find owner
g = requests.get("https://api.mercadolibre.com/items/MLM5244434174",headers=H,timeout=15).json()
print(f"=== MLM5244434174 ===")
print(f"  status: {g.get('status')}")
print(f"  title: {g.get('title','?')}")
print(f"  price: ${g.get('price')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  catalog_listing: {g.get('catalog_listing')}")
print(f"  category: {g.get('category_id')}")
print(f"  seller_id: {g.get('seller_id')}")
attrs = {a.get('id'):a.get('value_name','') for a in g.get('attributes',[]) or []}
print(f"  BRAND: {attrs.get('BRAND','')}")
print(f"  MODEL: {attrs.get('MODEL','')}")
print(f"  COLOR: {attrs.get('COLOR','')}")

cpid = g.get('catalog_product_id')
if cpid:
    print(f"\n=== Catálogo padre {cpid} ===")
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    print(f"  name: {p.get('name','')}")
    print(f"  domain: {p.get('domain_id','')}")

# Search for similar catalogs based on title
title = g.get('title','')
if title:
    print(f"\n=== Catálogos similares (basados en título) ===")
    # Extract main product name
    import re
    # Try various queries
    base_words = title.split()[:4]
    query = ' '.join(base_words)
    print(f"Query: '{query}'")
    r2 = requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={query.replace(' ','+')}&limit=30",headers=H,timeout=15).json()
    print(f"Total resultados: {r2.get('paging',{}).get('total','?')}")
    for prod in (r2.get("results",[]) or [])[:30]:
        pid = prod.get("id")
        name = prod.get("name","")[:80]
        domain = prod.get("domain_id","")
        marker = " 👈 ESTE" if pid == cpid else ""
        print(f"  {pid}: {name} ({domain}){marker}")
