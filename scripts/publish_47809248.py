#!/usr/bin/env python3
"""Publica MLM47809248 en Claribel con precio ganador (competidor más barato - $10)."""
import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

CPID = "MLM47809248"
QTY = 1
GAP = 10
FLOOR = 299
DAILY = 15

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')}\n")

# Get catalog details
print(f"=== Inspeccionando {CPID} ===")
p = requests.get(f"https://api.mercadolibre.com/products/{CPID}", headers=H, timeout=15).json()
title = (p.get("name") or "")[:60]
domain = p.get("domain_id","")
print(f"  title: '{title}'")
print(f"  domain: {domain}")
print(f"  category_id: {p.get('category_id')}")

# Get buy_box_winner + competitors
bbw = p.get("buy_box_winner") or {}
print(f"  buy_box_winner: {bbw.get('item_id','-')} ${bbw.get('price','-')}")

print(f"\n=== Competidores ===")
r2 = requests.get(f"https://api.mercadolibre.com/products/{CPID}/items?limit=20", headers=H, timeout=15).json()
competitors = r2.get("results",[]) or []
for c in competitors[:8]:
    iid = c.get("item_id"); price = c.get("price"); seller = c.get("seller_id")
    log = (c.get("shipping",{}) or {}).get("logistic_type","")
    print(f"  {iid} ${price} seller={seller} log={log}")

# Determine target price
target = None
ext_price = None
has_full = any((c.get("shipping",{}) or {}).get("logistic_type")=="fulfillment" for c in competitors)
if competitors:
    cheapest = min(competitors, key=lambda x: float(x.get("price") or 999999))
    ext_price = float(cheapest.get("price"))
    effective_gap = 80 if has_full else GAP
    target = max(FLOOR, ext_price - effective_gap)
    print(f"\n  Cheapest competitor: ${ext_price}")
    print(f"  has_full: {has_full} | gap: ${effective_gap}")
    print(f"  Target price (winning): ${target}")
else:
    target = 499  # fallback
    print(f"\n  Sin competidores — usando precio default $499")

CATEGORY = p.get("category_id") or "MLM1271"  # default perfumes

payload = {
    "title": title,
    "category_id": CATEGORY,
    "catalog_product_id": CPID,
    "catalog_listing": True,
    "price": target,
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

print(f"\n=== Publicando ===")
rp = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload, timeout=20)
print(f"POST → {rp.status_code}")
if rp.status_code in (200,201):
    j = rp.json()
    iid = j.get("id")
    print(f"✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
    print(f"   {j.get('permalink','')}")
    
    # Add to stock_config
    try: cfg = json.load(open("stock_config_claribel.json"))
    except: cfg = {}
    cfg[iid] = {
        "line": "Catalog-Claribel-Custom",
        "label": title[:45],
        "price": target,
        "catalog_product_id": CPID,
        "auto_replenish": True,
        "min_visible": 1,
        "real_stock": DAILY,
        "daily_reset_to": DAILY,
        "active": True,
        "condition": "new",
        "type": "catalog_no_variations"
    }
    with open("stock_config_claribel.json","w") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Añadido al stock_config_claribel.json")
    print(f"   real_stock={DAILY} | daily_reset_to={DAILY} | auto_replenish=true")
    print(f"   Throttle 70u/día Claribel: lo cuenta automáticamente")
else:
    err = rp.json() if rp.headers.get("content-type","").startswith("application/json") else rp.text
    print(f"❌ {json.dumps(err, ensure_ascii=False)[:500]}")
