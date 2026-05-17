import os, requests

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

print(f"Total items: {len(ids)}\n")

# Buscar items 35w con color lila/morado/violeta
print("=== Variantes 35W de la familia bocina (color hunting) ===")
candidates_35w = []
for i in range(0, len(ids), 20):
    r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(ids[i:i+20])}&attributes=id,title,price,available_quantity,sold_quantity,status,user_product_id,permalink,shipping", headers=h, timeout=20).json()
    for it in r:
        if it.get("code") == 200:
            b = it["body"]
            title = (b.get("title") or "").lower()
            if "35w" in title or "35 w" in title:
                candidates_35w.append(b)

print(f"Items con '35w' en title: {len(candidates_35w)}")
for b in candidates_35w:
    color_match = ""
    title_lower = (b.get('title') or '').lower()
    for c in ['rojo', 'azul', 'lila', 'morado', 'violeta', 'negro', 'verde', 'amarillo', 'rosa', 'blanco']:
        if c in title_lower:
            color_match = c.upper()
            break
    print(f"  {b['id']} | UP:{b.get('user_product_id','-')} | {color_match:<8} | status:{b.get('status'):<13} | qty:{b.get('available_quantity'):<3} | sold:{b.get('sold_quantity'):<3} | ${b.get('price')} | logistic:{b.get('shipping',{}).get('logistic_type','-')}")
    print(f"    URL: {b.get('permalink','')}")
