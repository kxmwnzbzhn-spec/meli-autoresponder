import os, requests, json

# Get tokens for BOTH accounts
def get_token(refresh_var):
    return requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID"],
        "client_secret": os.environ["MELI_APP_SECRET"],
        "refresh_token": os.environ[refresh_var]
    }, timeout=20).json()["access_token"]

# Lookup catalog product
print("=== Catálogo product MLM45458769 ===")
r = requests.get("https://api.mercadolibre.com/products/MLM45458769", timeout=15).json()
print(f"  Name: {r.get('name')}")
print(f"  Family: {r.get('family_name')}")
print(f"  Domain: {r.get('domain_id')}")
print(f"  Status: {r.get('status')}")
print(f"  Buy Box winner: {r.get('buy_box_winner', {}).get('seller_id', '?')}")
print(f"  Catalog ID: {r.get('id')}")

# Try to get pictures
pics = r.get('pictures', [])
print(f"  Pictures count: {len(pics)}")
for i, p in enumerate(pics[:8], 1):
    print(f"    {i}. {p.get('secure_url') or p.get('url')}")

# Find Wilbert + ASVAELECTRONICS items with this catalog_product_id
for label, refresh in [("ASVAELECTRONICS (1668713481)", "MELI_REFRESH_TOKEN_USER1668"), ("WILBERT (3367276814)", "MELI_REFRESH_TOKEN_WILBERT")]:
    try:
        tok = get_token(refresh)
        h = {"Authorization": f"Bearer {tok}"}
        uid = "1668713481" if "USER1668" in refresh else "3367276814"
        
        # Get all items
        ids = []; offset = 0
        while True:
            j = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?limit=50&offset={offset}", headers=h, timeout=20).json()
            res = j.get("results", [])
            if not res: break
            ids.extend(res)
            if len(res) < 50: break
            offset += 50
        
        # Buscar items con catalog_product_id = MLM45458769
        matches = []
        for i in range(0, len(ids), 20):
            r2 = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(ids[i:i+20])}&attributes=id,title,price,available_quantity,sold_quantity,status,catalog_product_id,permalink,shipping", headers=h, timeout=20).json()
            for it in r2:
                if it.get("code") == 200:
                    b = it["body"]
                    if b.get("catalog_product_id") == "MLM45458769":
                        matches.append(b)
        
        print(f"\n=== {label}: {len(matches)} match(es) ===")
        for m in matches:
            print(f"  {m['id']} | status:{m.get('status')} | qty:{m.get('available_quantity')} | sold:{m.get('sold_quantity')} | ${m.get('price')} | {m.get('title','')[:55]}")
            print(f"    Logistic: {m.get('shipping',{}).get('logistic_type')}")
            print(f"    URL: {m.get('permalink')}")
    except Exception as e:
        print(f"  ERR {label}: {e}")
