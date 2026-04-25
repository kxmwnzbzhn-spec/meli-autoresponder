import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# 1) Estado del item MLM5245310490
print("=== MLM5245310490 (Claribel Camuflaje) ===")
g = requests.get("https://api.mercadolibre.com/items/MLM5245310490", headers=H).json()
print(f"  status: {g.get('status')}")
print(f"  price: ${g.get('price')}")
print(f"  available_quantity: {g.get('available_quantity')}")
print(f"  sold_quantity: {g.get('sold_quantity')}")
print(f"  free_shipping: {g.get('shipping',{}).get('free_shipping')}")
print(f"  shipping mode: {g.get('shipping',{}).get('mode')}")
print(f"  shipping logistic_type: {g.get('shipping',{}).get('logistic_type')}")
print(f"  catalog_listing: {g.get('catalog_listing')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  health: {g.get('health')}")
print(f"  tags: {g.get('tags')}")
print(f"  sub_status: {g.get('sub_status')}")

# 2) Catalog product winner detail
cpid = "MLM37361021"
print(f"\n=== Catalog {cpid} buy_box_winner ===")
p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H).json()
bbw = p.get("buy_box_winner")
if bbw:
    print(f"  WINNER: {bbw.get('item_id')}")
    print(f"    price: ${bbw.get('price')}")
    print(f"    seller_id: {bbw.get('seller_id')}")
    print(f"    shipping: {bbw.get('shipping')}")
    print(f"    sold_quantity: {bbw.get('sold_quantity')}")

# 3) ALL competitors ordered
print(f"\n=== Competidores en {cpid} ===")
r2 = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=20", headers=H).json()
for c in r2.get("results",[])[:10]:
    iid = c.get("item_id")
    price = c.get("price")
    seller = c.get("seller_id")
    free = c.get("shipping",{}).get("free_shipping") if c.get("shipping") else None
    cond = c.get("condition")
    print(f"  {iid} ${price} seller={seller} free={free} cond={cond}")

# 4) Why we're winning_eligible?
print(f"\n=== /products/{cpid}/eligible_for_buy_box?item_id=MLM5245310490 ===")
try:
    r3 = requests.get(f"https://api.mercadolibre.com/items/MLM5245310490/catalog_listings_status", headers=H).json()
    print(json.dumps(r3, indent=2)[:1500])
except Exception as e:
    print(f"err: {e}")
