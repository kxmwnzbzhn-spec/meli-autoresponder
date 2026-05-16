import os, requests, json

tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_WILBERT"]
}, timeout=20).json()["access_token"]

h = {"Authorization": f"Bearer {tok}"}

# Get user_product info
print("=== User Product MLMU3924350150 ===")
r = requests.get(f"https://api.mercadolibre.com/user-products/MLMU3924350150", headers=h, timeout=15).json()
print(json.dumps(r, indent=2, ensure_ascii=False)[:1500])

print("\n=== Buscar items del seller con 35W y bass ===")
# Lista items del seller
all_items = []
offset = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/users/3367276814/items/search?status=active&limit=50&offset={offset}", headers=h, timeout=20).json()
    results = j.get("results", [])
    if not results: break
    all_items.extend(results)
    if len(results) < 50: break
    offset += 50
print(f"Seller tiene {len(all_items)} items activos total")

# Buscar details de items con keywords match
print("\n=== Items con 35W o Bass + Azul ===")
matches = []
for i in range(0, len(all_items), 20):
    batch = all_items[i:i+20]
    r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(batch)}&attributes=id,title,price,available_quantity,sold_quantity,status,permalink,user_product_id", headers=h, timeout=20).json()
    for it in r:
        if it.get("code") == 200:
            b = it["body"]
            title = (b.get("title") or "").lower()
            upid = b.get("user_product_id", "")
            if upid == "MLMU3924350150" or ("35w" in title or "35 w" in title) and "azul" in title:
                matches.append(b)

print(f"\nMatches encontrados: {len(matches)}")
for m in matches:
    print(f"\n--- {m['id']} ---")
    print(f"  Title:  {m.get('title')}")
    print(f"  Price:  ${m.get('price')}")
    print(f"  Stock:  {m.get('available_quantity')} (vendidas: {m.get('sold_quantity')})")
    print(f"  Status: {m.get('status')}")
    print(f"  UP ID:  {m.get('user_product_id')}")
    print(f"  URL:    {m.get('permalink')}")
