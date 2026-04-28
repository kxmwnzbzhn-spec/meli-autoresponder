"""
Clonar 5 items específicos Claribel → Mildred.
Solo catalog_listing=true. Stock 1 visible / 15 real.
"""
import os, requests, json, time

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT_C = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
RT_M = os.environ["MELI_REFRESH_TOKEN_MILDRED"]

ITEMS_TO_CLONE = [
    "MLM5241635216", "MLM5241631618", "MLM5241335830",
    "MLM5241336574", "MLM5244431430",
]

# Auth Claribel
r1 = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_C}).json()
H_C = {"Authorization":f"Bearer {r1['access_token']}","Content-Type":"application/json"}
me_c = requests.get("https://api.mercadolibre.com/users/me",headers=H_C).json()
print(f"Claribel: {me_c.get('nickname')} ({me_c.get('id')})")

# Auth Mildred
r2 = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_M}).json()
H_M = {"Authorization":f"Bearer {r2['access_token']}","Content-Type":"application/json"}
me_m = requests.get("https://api.mercadolibre.com/users/me",headers=H_M).json()
USER_M = me_m["id"]
print(f"Mildred: {me_m.get('nickname')} ({USER_M})\n")

# Get info de cada item Claribel
to_publish = []
for iid in ITEMS_TO_CLONE:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,category_id,status",headers=H_C,timeout=10).json()
    if g.get("status") == "error" or "id" not in g:
        print(f"  ❌ {iid}: NO encontrado en Claribel ({g.get('message','')})")
        continue
    cl = g.get("catalog_listing")
    cpid = g.get("catalog_product_id")
    if not cl:
        print(f"  ⏭️  {iid}: NO catálogo (catalog_listing={cl}) — SKIP")
        continue
    if not cpid:
        print(f"  ⏭️  {iid}: catálogo sin cpid — SKIP")
        continue
    print(f"  ✅ {iid}: catálogo cpid={cpid} ${g.get('price')} | '{g.get('title','')[:55]}'")
    to_publish.append({
        "iid_claribel": iid,
        "cpid": cpid,
        "title": g.get("title",""),
        "price": g.get("price"),
        "category_id": g.get("category_id"),
    })

print(f"\nTotal a clonar: {len(to_publish)}\n")

# Check existing en Mildred (skip duplicados)
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

# Load Mildred config
try: cfg = json.load(open("stock_config_mildred.json"))
except: cfg = {}

published = []; skipped = []; errors = []

for i, item in enumerate(to_publish, 1):
    cpid = item["cpid"]
    if cpid in existing_cpids:
        print(f"[{i}/{len(to_publish)}] {cpid} skip (ya en Mildred)")
        skipped.append(cpid); continue

    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H_M,timeout=15).json()
    title = (p.get("name") or item["title"])[:60]
    target_price = item["price"] or 499

    payload = {
        "title": title,
        "category_id": item["category_id"],
        "catalog_product_id": cpid,
        "catalog_listing": True,
        "price": target_price,
        "available_quantity": 1,
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
        print(f"[{i}/{len(to_publish)}] ✅ {iid_m} ← {cpid} ${target_price} | '{title[:40]}'")
        published.append({"iid":iid_m,"cpid":cpid,"price":target_price,"title":title})
        cfg[iid_m] = {
            "line": "Catalog-Mildred-Claribel-Clone",
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
        print(f"[{i}/{len(to_publish)}] ❌ {cpid}: {json.dumps(err,ensure_ascii=False)[:300]}")
        errors.append({"cpid":cpid,"err":err})

    if i < len(to_publish): time.sleep(5)

with open("stock_config_mildred.json","w") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Publicados: {len(published)}")
print(f"⏭️  Skipped (ya existían): {len(skipped)}")
print(f"❌ Errores: {len(errors)}")
print(f"{'='*60}")
