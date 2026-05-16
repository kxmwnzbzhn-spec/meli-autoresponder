import os, requests, json

# Refresh access_token usando refresh_token de GH Secret
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
access = tok["access_token"]
print(f"✓ Access token nuevo obtenido (user_id: {tok.get('user_id')})")

h = {"Authorization": f"Bearer {access}"}

# 1) User product MLMU3924350212
print(f"\n=== User Product MLMU3924350212 (rojo) ===")
r = requests.get("https://api.mercadolibre.com/user-products/MLMU3924350212", headers=h, timeout=15).json()
print(f"  Name:    {r.get('name')}")
print(f"  user_id: {r.get('user_id')}")
print(f"  Family:  {r.get('family_name')}")

# 2) Items totales (sin filtro)
print(f"\n=== Items totales del seller ===")
ids = []; offset = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/users/1668713481/items/search?limit=50&offset={offset}", headers=h, timeout=20).json()
    res = j.get("results", [])
    if not res: break
    ids.extend(res)
    if len(res) < 50: break
    offset += 50
print(f"Total items: {len(ids)}")

# Detalles
found_red = None
print(f"\nListado completo:")
for i in range(0, len(ids), 20):
    r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(ids[i:i+20])}&attributes=id,title,price,available_quantity,sold_quantity,status,sub_status,user_product_id,permalink,shipping,pictures", headers=h, timeout=20).json()
    for it in r:
        if it.get("code") == 200:
            b = it["body"]
            color_match = "🔴 ROJO" if "rojo" in b.get('title','').lower() else ""
            up_match = "★ MATCH" if b.get('user_product_id') == "MLMU3924350212" else ""
            print(f"  {b['id']} | UP:{b.get('user_product_id','-'):<15} | {b.get('status','?'):<8} | qty:{b.get('available_quantity','-'):<3} | sold:{b.get('sold_quantity','-'):<3} | ${b.get('price','-'):<5} | {b.get('title','')[:48]} {color_match} {up_match}")
            if b.get('user_product_id') == "MLMU3924350212":
                found_red = b

if found_red:
    print(f"\n★★★ LISTING ROJO ENCONTRADO ★★★")
    print(f"  MLM ID:    {found_red['id']}")
    print(f"  URL:       {found_red.get('permalink')}")
    print(f"  Stock:     {found_red.get('available_quantity')}")
    print(f"  Sold:      {found_red.get('sold_quantity')}")
    print(f"  Logistic:  {found_red.get('shipping',{}).get('logistic_type')}")
    print(f"  Status:    {found_red.get('status')}")
    print(f"\n  FOTOS ({len(found_red.get('pictures',[]))}):")
    for i, p in enumerate(found_red.get('pictures',[]), 1):
        print(f"    {i}. {p.get('secure_url')}")
