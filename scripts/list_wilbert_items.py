import os, requests, json
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_WILBERT"]
}, timeout=20).json()["access_token"]
h = {"Authorization": f"Bearer {tok}"}

all_items = []
offset = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/users/3367276814/items/search?status=active&limit=50&offset={offset}", headers=h, timeout=20).json()
    results = j.get("results", [])
    if not results: break
    all_items.extend(results)
    if len(results) < 50: break
    offset += 50

# Get full details
details = []
for i in range(0, len(all_items), 20):
    r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(all_items[i:i+20])}&attributes=id,title,price,available_quantity,sold_quantity", headers=h, timeout=25).json()
    for it in r:
        if it.get("code") == 200:
            details.append(it["body"])

details.sort(key=lambda x: -x.get("sold_quantity", 0))

print(f"=== TODOS los items activos de Wilbert (top 20 por ventas) ===\n")
print(f"{'#':>2}  {'MLM_ID':<14}  {'Price':>7}  {'Sold':>4}  Title")
print(f"{'-'*2}  {'-'*14}  {'-'*7}  {'-'*4}  {'-'*70}")
for i, d in enumerate(details[:20], 1):
    title = (d.get('title') or '')[:65]
    print(f"{i:>2}. {d['id']:<14}  ${d.get('price', 0):>6,.0f}  {d.get('sold_quantity', 0):>4}  {title}")
