import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
sid = me["id"]

ids = []
s = 0
while True:
    d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}", headers=H).json()
    got = d.get("results", []) or []
    if not got: break
    ids.extend(got); s += 100
    if s >= d.get("paging",{}).get("total",0): break

print(f"=== Juan: {len(ids)} items activos ===")
items_data = []
for iid in ids:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = item.get("title","")
    avail = item.get("available_quantity",0)
    sold = item.get("sold_quantity",0)
    price = item.get("price",0)
    cpid = item.get("catalog_product_id","")
    print(f"  {iid:>16} | avail={avail:>4} sold={sold:>4} | ${int(price):>5} | cpid={cpid or '-':>14} | {title[:60]}")
    items_data.append({"iid":iid, "title":title, "avail":avail, "sold":sold, "price":price})

# Exportar para uso posterior
import json
with open("/tmp/juan_items.json","w") as f:
    json.dump(items_data, f, indent=2, ensure_ascii=False)
