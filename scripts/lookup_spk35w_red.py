import os, requests, json

tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}

# Get all items
ids = []; offset = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/users/1668713481/items/search?limit=50&offset={offset}", headers=h, timeout=20).json()
    res = j.get("results", [])
    if not res: break
    ids.extend(res)
    if len(res) < 50: break
    offset += 50

found_red = None
all_35w_red = []

for i in range(0, len(ids), 20):
    r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(ids[i:i+20])}&attributes=id,title,price,available_quantity,sold_quantity,status,user_product_id,permalink,shipping,pictures", headers=h, timeout=20).json()
    for it in r:
        if it.get("code") == 200:
            b = it["body"]
            up = b.get("user_product_id") or ""
            title = b.get("title") or ""
            # Match exact UP
            if up == "MLMU3924350212":
                found_red = b
            # Match 35w + rojo en title (backup)
            if "35w" in title.lower() and "rojo" in title.lower():
                all_35w_red.append(b)

if found_red:
    print(f"★★★ LISTING ROJO MLMU3924350212 ENCONTRADO ★★★")
    print(f"  MLM ID:    {found_red['id']}")
    print(f"  Title:     {found_red.get('title')}")
    print(f"  Price:     ${found_red.get('price')}")
    print(f"  Stock:     {found_red.get('available_quantity')}")
    print(f"  Sold:      {found_red.get('sold_quantity')}")
    print(f"  Status:    {found_red.get('status')}")
    print(f"  Logistic:  {found_red.get('shipping',{}).get('logistic_type')}")
    print(f"  URL:       {found_red.get('permalink')}")
    print(f"  FOTOS:")
    for i, p in enumerate(found_red.get('pictures',[]), 1):
        print(f"    {i}. {p.get('secure_url')}")
elif all_35w_red:
    print(f"⚠️ No match exacto del UP MLMU3924350212. Pero hay {len(all_35w_red)} items con '35w rojo' en title:")
    for b in all_35w_red:
        print(f"  {b['id']} | UP:{b.get('user_product_id')} | status:{b.get('status')} | qty:{b.get('available_quantity')} | sold:{b.get('sold_quantity')} | {b.get('title')}")
else:
    print(f"✗ No encontré ninguno. Verificar UP del listing rojo manualmente.")

print(f"\n=== Estado del AZUL (MLM5233454100) ===")
r = requests.get("https://api.mercadolibre.com/items/MLM5233454100?attributes=id,status,sub_status,available_quantity,sold_quantity", headers=h, timeout=15).json()
print(f"  Status:    {r.get('status')}")
print(f"  Sub:       {r.get('sub_status')}")
print(f"  qty:       {r.get('available_quantity')}")
print(f"  sold:      {r.get('sold_quantity')}")
