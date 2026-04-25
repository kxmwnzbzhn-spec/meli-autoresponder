import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")

# Try Juan's token
RT_JUAN = os.getenv("MELI_REFRESH_TOKEN","")
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_JUAN
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Token Juan: {me.get('nickname')} ({me.get('id')})")

print("\n=== MLM5244431296 (con token Juan) ===")
g = requests.get("https://api.mercadolibre.com/items/MLM5244431296", headers=H).json()
print(f"  status: {g.get('status')}")
print(f"  title: {g.get('title','?')}")
print(f"  cond: {g.get('condition')}")
print(f"  price: ${g.get('price')}")
print(f"  cat: {g.get('category_id')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  seller_id: {g.get('seller_id')}")
print(f"  qty: {g.get('available_quantity')}")
attrs = {a.get('id'):a.get('value_name','') for a in g.get('attributes',[]) or []}
print(f"  BRAND: {attrs.get('BRAND','')}")
print(f"  MODEL: {attrs.get('MODEL','')}")
print(f"  pictures: {len(g.get('pictures',[]) or [])}")
for p in (g.get('pictures',[]) or [])[:3]:
    print(f"    pic: {p.get('id')} {p.get('url','')[:60]}")

# Try public access
print("\n=== MLM5244431296 (sin auth, público) ===")
g2 = requests.get("https://api.mercadolibre.com/items/MLM5244431296").json()
print(f"  status: {g2.get('status')}")
print(f"  title: {g2.get('title','?')}")
print(f"  seller: {g2.get('seller_id')}")
