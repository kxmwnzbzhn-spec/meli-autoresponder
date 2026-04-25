#!/usr/bin/env python3
"""Publica 2 catálogos JBL Go 4 ROJO en Claribel + agrega al stock_config."""
import os, requests, json, time

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

CATALOGS = [
    "MLM47119316",  # Altavoz Bluetooth JBL GO 4 Portátil Impermeable en Rojo
    "MLM64389753",  # Jbl Go 4 - Altavoz Ultraportátil Bluetooth Color Rojo
]
PRICE = 499.0
QTY = 1
CATEGORY = "MLM59800"
DELAY_BETWEEN = 8
LINE = "Catalog-Claribel-Rojo"

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}

published = []; errors = []

for i, cpid in enumerate(CATALOGS, 1):
    print(f"\n=== [{i}/{len(CATALOGS)}] {cpid} ===")
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
        published.append({"cpid":cpid,"iid":iid,"title":title})
        cfg[iid] = {
            "line": LINE, "label": title[:45], "price": PRICE,
            "catalog_product_id": cpid, "auto_replenish": True,
            "min_visible": 1, "real_stock": 10, "daily_reset_to": 10,
            "active": True, "condition": "new", "type": "catalog_no_variations"
        }
    else:
        err = rp.json() if rp.headers.get("content-type","").startswith("application/json") else rp.text
        print(f"  ❌ {rp.status_code}: {json.dumps(err, ensure_ascii=False)[:400]}")
        errors.append({"cpid":cpid,"err":err})
    if i < len(CATALOGS):
        time.sleep(DELAY_BETWEEN)

with open("stock_config_claribel.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}\n✅ Publicados: {len(published)} | ❌ Errores: {len(errors)}\n{'='*60}")
for p in published:
    print(f"  {p['iid']} ← {p['cpid']} | {p['title'][:40]}")
