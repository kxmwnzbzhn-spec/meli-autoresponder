#!/usr/bin/env python3
"""Publica 11 catálogos JBL Go 4 AZUL en Claribel + agrega al stock_config."""
import os, requests, json, time

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

CATALOGS_AZUL = [
    "MLM37922010", "MLM37986357", "MLM44710397", "MLM44742229", "MLM44831552",
    "MLM45829435", "MLM46140333", "MLM59314557", "MLM62020842", "MLM63258207",
    "MLM64277118"
]
PRICE = 499.0
QTY = 1   # visible MELI
CATEGORY = "MLM59800"
DELAY_BETWEEN = 8  # segundos entre cada publicación

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

# Load existing config
try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}

published = []
errors = []

for i, cpid in enumerate(CATALOGS_AZUL, 1):
    print(f"\n=== [{i}/{len(CATALOGS_AZUL)}] {cpid} ===")
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=15).json()
    title = (p.get("name") or "")[:60]
    print(f"  title: '{title}'")
    
    payload = {
        "title": title,
        "category_id": CATEGORY,
        "catalog_product_id": cpid,
        "catalog_listing": True,
        "price": PRICE,
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
    
    rp = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload, timeout=20)
    if rp.status_code in (200,201):
        j = rp.json()
        iid = j.get("id")
        print(f"  ✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
        print(f"     {j.get('permalink','')}")
        published.append({"cpid": cpid, "iid": iid, "title": title})
        # Add to stock_config
        cfg[iid] = {
            "line": "Catalog-Claribel-Azul",
            "label": title[:45],
            "price": PRICE,
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
        print(f"  ❌ {rp.status_code}: {json.dumps(err, ensure_ascii=False)[:400]}")
        errors.append({"cpid": cpid, "status": rp.status_code, "err": err})
    
    if i < len(CATALOGS_AZUL):
        print(f"  💤 sleep {DELAY_BETWEEN}s...")
        time.sleep(DELAY_BETWEEN)

# Save updated config
with open("stock_config_claribel.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Publicados: {len(published)}")
print(f"❌ Errores: {len(errors)}")
print(f"{'='*60}")
for p in published:
    print(f"  {p['iid']} ← catalog {p['cpid']} | {p['title'][:40]}")
if errors:
    print(f"\nErrores:")
    for e in errors:
        print(f"  {e['cpid']}: {str(e['err'])[:200]}")
