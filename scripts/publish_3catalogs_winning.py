#!/usr/bin/env python3
"""Publica 3 catálogos en Claribel con precio ganador automático."""
import os, requests, json, time
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

CATALOGS = ["MLM62279317", "MLM61631985", "MLM59802579"]
QTY = 1
GAP = 10
FLOOR = 299
DAILY = 15
DELAY = 8

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')}\n")

try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}

published = []; errors = []

for i, CPID in enumerate(CATALOGS, 1):
    print(f"\n{'='*60}\n=== [{i}/{len(CATALOGS)}] {CPID} ===\n{'='*60}")
    p = requests.get(f"https://api.mercadolibre.com/products/{CPID}", headers=H, timeout=15).json()
    title = (p.get("name") or "")[:60]
    domain = p.get("domain_id","")
    print(f"  title: '{title}'")
    print(f"  domain: {domain}")
    
    # Find category from competitor (since p.category_id is None for many)
    r2 = requests.get(f"https://api.mercadolibre.com/products/{CPID}/items?limit=20", headers=H, timeout=15).json()
    competitors = r2.get("results",[]) or []
    
    # Get cat from first competitor
    category = None
    if competitors:
        ref_iid = competitors[0].get("item_id")
        ri = requests.get(f"https://api.mercadolibre.com/items/{ref_iid}?attributes=category_id", headers=H, timeout=10).json()
        category = ri.get("category_id")
    if not category:
        # Default by domain
        if domain == "MLM-SPEAKERS": category = "MLM59800"
        elif domain == "MLM-PERFUMES": category = "MLM1271"
        else: category = "MLM59800"
    print(f"  category: {category}")
    
    # Pricing
    has_full = any((c.get("shipping",{}) or {}).get("logistic_type")=="fulfillment" for c in competitors)
    target = None; ext_price = None
    if competitors:
        cheapest = min(competitors, key=lambda x: float(x.get("price") or 999999))
        ext_price = float(cheapest.get("price"))
        effective_gap = 80 if has_full else GAP
        target = max(FLOOR, ext_price - effective_gap)
        print(f"  Cheapest: ${ext_price} | has_full: {has_full} | gap: ${effective_gap}")
    else:
        target = 499
        print(f"  Sin competidores — fallback $499")
    print(f"  Target: ${target}")
    
    # Show top competitors
    print(f"  Top competitors:")
    for c in competitors[:5]:
        print(f"    {c.get('item_id')} ${c.get('price')} log={(c.get('shipping',{}) or {}).get('logistic_type','')}")
    
    payload = {
        "title": title,
        "category_id": category,
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
    rp = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload, timeout=20)
    print(f"  POST → {rp.status_code}")
    if rp.status_code in (200,201):
        j = rp.json()
        iid = j.get("id")
        print(f"  ✅ {iid} | ${j.get('price')}")
        print(f"     {j.get('permalink','')}")
        published.append({"cpid":CPID,"iid":iid,"title":title,"price":target})
        cfg[iid] = {
            "line": "Catalog-Claribel-Custom2",
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
    else:
        err = rp.json() if rp.headers.get("content-type","").startswith("application/json") else rp.text
        print(f"  ❌ {json.dumps(err, ensure_ascii=False)[:600]}")
        errors.append({"cpid":CPID,"err":err})
    if i < len(CATALOGS): time.sleep(DELAY)

with open("stock_config_claribel.json","w") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}\n✅ Publicados: {len(published)} | ❌ Errores: {len(errors)}\n{'='*60}")
for p in published:
    print(f"  {p['iid']} ← {p['cpid']} ${p['price']} | {p['title'][:40]}")
