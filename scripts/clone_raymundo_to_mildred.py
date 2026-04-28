"""
Clonar todos los catálogos de Raymundo → Mildred.
- Stock visible MELI: 1
- Stock real (bot): 15
- auto_replenish: True
- min_visible: 1
"""
import os, requests, json, time

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT_R = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
RT_M = os.environ["MELI_REFRESH_TOKEN_MILDRED"]

DELAY = 6  # entre publicaciones

# Auth Raymundo (origen)
r1 = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_R}).json()
H_R = {"Authorization":f"Bearer {r1['access_token']}","Content-Type":"application/json"}
me_r = requests.get("https://api.mercadolibre.com/users/me",headers=H_R).json()
USER_R = me_r["id"]
print(f"Origen: {me_r.get('nickname')} ({USER_R})")

# Get TODOS los items de Raymundo (active + paused)
all_ids = set()
for st in ("active","paused"):
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_R}/items/search?status={st}&limit=50&offset={offset}",headers=H_R,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        all_ids.update(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

print(f"Total items Raymundo: {len(all_ids)}")

# Filtrar solo catálogos (con cpid)
to_clone = []
for iid in all_ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,category_id",headers=H_R,timeout=10).json()
    if not g.get("catalog_listing"): continue
    cpid = g.get("catalog_product_id")
    if not cpid: continue
    to_clone.append({
        "iid_raymundo": iid,
        "cpid": cpid,
        "title": g.get("title",""),
        "price": g.get("price"),
        "category_id": g.get("category_id","MLM59800"),
    })

print(f"Catálogos a clonar: {len(to_clone)}\n")

# Auth Mildred (destino)
r2 = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_M}).json()
H_M = {"Authorization":f"Bearer {r2['access_token']}","Content-Type":"application/json"}
me_m = requests.get("https://api.mercadolibre.com/users/me",headers=H_M).json()
USER_M = me_m["id"]
print(f"Destino: {me_m.get('nickname')} ({USER_M})\n")

# Check qué cpids ya existen en Mildred
existing_cpids = set()
ids_m = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_M}/items/search?limit=50&offset={offset}",headers=H_M,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids_m.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
for iid in ids_m:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=catalog_product_id",headers=H_M,timeout=10).json()
    cpid = g.get("catalog_product_id")
    if cpid: existing_cpids.add(cpid)
print(f"Mildred ya tiene {len(existing_cpids)} cpids\n")

# Load config Mildred
try: cfg = json.load(open("stock_config_mildred.json"))
except: cfg = {}

published = []
skipped = []
errors = []

for i, item in enumerate(to_clone, 1):
    cpid = item["cpid"]
    if cpid in existing_cpids:
        print(f"[{i}/{len(to_clone)}] {cpid} skip (ya en Mildred)")
        skipped.append(cpid); continue
    
    # Pull product info from Mildred token (puede ser publicación catalog_listing)
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H_M,timeout=15).json()
    title = (p.get("name") or item["title"])[:60]
    target_price = item["price"] or 499
    
    payload = {
        "title": title,
        "category_id": item["category_id"],
        "catalog_product_id": cpid,
        "catalog_listing": True,
        "price": target_price,
        "available_quantity": 1,  # 1 a la vista
        "currency_id": "MXN",
        "condition": "new",
        "listing_type_id": "gold_special",
        "sale_terms": [
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
        "shipping": {"mode":"me2","free_shipping":False,"tags":["self_service_in"]},
    }
    
    rp = requests.post("https://api.mercadolibre.com/items",headers=H_M,json=payload,timeout=25)
    if rp.status_code in (200,201):
        j = rp.json(); iid_m = j.get("id")
        print(f"[{i}/{len(to_clone)}] ✅ {iid_m} ← {cpid} ${target_price} | '{title[:40]}'")
        published.append({"iid":iid_m,"cpid":cpid,"price":target_price,"title":title})
        cfg[iid_m] = {
            "line": "Catalog-Mildred-Bocina",
            "label": title[:45],
            "price": target_price,
            "catalog_product_id": cpid,
            "auto_replenish": True,
            "min_visible": 1,
            "real_stock": 15,
            "daily_reset_to": 15,
            "active": True,
            "condition": "new",
            "type": "catalog_no_variations",
        }
    else:
        try: err = rp.json()
        except: err = rp.text
        print(f"[{i}/{len(to_clone)}] ❌ {cpid}: {json.dumps(err,ensure_ascii=False)[:300]}")
        errors.append({"cpid":cpid,"err":err})
    
    if i < len(to_clone): time.sleep(DELAY)

# Save Mildred config
with open("stock_config_mildred.json","w") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Publicados: {len(published)}")
print(f"⏭️  Skipped (ya existían): {len(skipped)}")
print(f"❌ Errores: {len(errors)}")
print(f"{'='*60}")
