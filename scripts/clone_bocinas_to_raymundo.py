#!/usr/bin/env python3
"""Clona catálogos de bocinas de Claribel → Raymundo. Skip perfumes y otros."""
import os, requests, json, time
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT_R = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
RT_C = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

PRICE = 499.0  # default
QTY = 1
DELAY = 8

# Auth Claribel: get catalog items
r1 = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_C}).json()
H_C = {"Authorization":f"Bearer {r1['access_token']}","Content-Type":"application/json"}
me_c = requests.get("https://api.mercadolibre.com/users/me",headers=H_C).json()
USER_C = me_c["id"]

# Find Claribel speaker catalogs (category MLM59800)
print("=== Identificando bocinas en Claribel ===")
ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_C}/items/search?status=active&limit=50&offset={offset}",headers=H_C,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

bocinas_to_clone = []
for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,category_id",headers=H_C,timeout=10).json()
    if not g.get("catalog_listing"): continue
    if g.get("category_id") != "MLM59800": continue  # solo bocinas
    cpid = g.get("catalog_product_id")
    if not cpid: continue
    bocinas_to_clone.append({"iid_claribel":iid,"cpid":cpid,"title":g.get("title",""),"price":g.get("price")})

print(f"Total bocinas catalog en Claribel: {len(bocinas_to_clone)}")
for b in bocinas_to_clone:
    print(f"  {b['cpid']} | ${b['price']} | '{b['title'][:55]}'")

# Auth Raymundo
r2 = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_R}).json()
H_R = {"Authorization":f"Bearer {r2['access_token']}","Content-Type":"application/json"}
me_r = requests.get("https://api.mercadolibre.com/users/me",headers=H_R).json()
USER_R = me_r["id"]
print(f"\n=== Publicando en Raymundo ({me_r.get('nickname')}) ===")

# Load Raymundo's stock_config
try: cfg = json.load(open("stock_config_raymundo.json"))
except: cfg = {}

# Check which Raymundo already has
already_in_raymundo = set()
ids_r = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_R}/items/search?status=active&limit=50&offset={offset}",headers=H_R,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids_r.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
for iid in ids_r:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=catalog_product_id",headers=H_R,timeout=10).json()
    cpid = g.get("catalog_product_id")
    if cpid: already_in_raymundo.add(cpid)
print(f"Raymundo ya tiene {len(already_in_raymundo)} catálogos\n")

published = []; errors = []; skipped = 0
for i, item in enumerate(bocinas_to_clone, 1):
    cpid = item["cpid"]
    if cpid in already_in_raymundo:
        print(f"[{i}/{len(bocinas_to_clone)}] {cpid} skip (ya existe en Raymundo)")
        skipped += 1
        continue
    
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H_R,timeout=15).json()
    title = (p.get("name") or item["title"])[:60]
    
    # Initial price = Claribel's + $20 (escalón) — catalog war ajustará despues
    target_price = (item["price"] or PRICE) + 20
    
    payload = {
        "title": title,
        "category_id": "MLM59800",
        "catalog_product_id": cpid,
        "catalog_listing": True,
        "price": target_price,
        "available_quantity": QTY,
        "currency_id": "MXN",
        "condition": "new",
        "listing_type_id": "gold_special",
        "sale_terms": [
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"}
        ],
        "shipping": {"mode":"me2","free_shipping":False,"tags":["self_service_in"]}
    }
    
    rp = requests.post("https://api.mercadolibre.com/items",headers=H_R,json=payload,timeout=20)
    if rp.status_code in (200,201):
        j = rp.json(); iid_r = j.get("id")
        print(f"[{i}/{len(bocinas_to_clone)}] ✅ {iid_r} ← {cpid} ${target_price} | '{title[:40]}'")
        published.append({"iid":iid_r,"cpid":cpid,"price":target_price,"title":title})
        cfg[iid_r] = {
            "line": "Catalog-Raymundo-Bocina-Failover",
            "label": title[:45],
            "price": target_price,
            "catalog_product_id": cpid,
            "auto_replenish": True,
            "min_visible": 1,
            "real_stock": 10,
            "daily_reset_to": 10,
            "active": True,
            "condition": "new",
            "type": "catalog_no_variations"
        }
    else:
        err = rp.json() if rp.headers.get("content-type","").startswith("application/json") else rp.text
        print(f"[{i}/{len(bocinas_to_clone)}] ❌ {cpid}: {json.dumps(err,ensure_ascii=False)[:300]}")
        errors.append({"cpid":cpid,"err":err})
    
    if i < len(bocinas_to_clone): time.sleep(DELAY)

# Save raymundo config
with open("stock_config_raymundo.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)

print(f"\n{'='*60}\n✅ Publicados: {len(published)}\n⏭️  Skipped (ya existían): {skipped}\n❌ Errores: {len(errors)}\n{'='*60}")
