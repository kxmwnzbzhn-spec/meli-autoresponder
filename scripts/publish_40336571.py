import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

CPID = "MLM40336571"
PRICE = 149.0
QTY = 1
REAL_STOCK = 150

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')}")

# Get catalog details
p = requests.get(f"https://api.mercadolibre.com/products/{CPID}", headers=H, timeout=15).json()
title = (p.get("name") or "")[:60]
domain = p.get("domain_id","")
print(f"\n=== {CPID} ===")
print(f"  title: '{title}'")
print(f"  domain: {domain}")

# Find category from competitor
r2 = requests.get(f"https://api.mercadolibre.com/products/{CPID}/items?limit=10",headers=H,timeout=15).json()
competitors = r2.get("results",[]) or []
category = None
if competitors:
    ref = competitors[0].get("item_id")
    ri = requests.get(f"https://api.mercadolibre.com/items/{ref}?attributes=category_id",headers=H,timeout=10).json()
    category = ri.get("category_id")
if not category:
    if domain == "MLM-SPEAKERS": category = "MLM59800"
    elif domain == "MLM-PERFUMES": category = "MLM1271"
    else: category = "MLM59800"
print(f"  category: {category}")
print(f"  competidores top:")
for c in competitors[:5]:
    print(f"    {c.get('item_id')} ${c.get('price')} log={(c.get('shipping',{}) or {}).get('logistic_type','')}")

payload = {
    "title": title,
    "category_id": category,
    "catalog_product_id": CPID,
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
print(f"\n=== Publicando a ${PRICE} ===")
rp = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload, timeout=20)
print(f"POST → {rp.status_code}")
if rp.status_code in (200,201):
    j = rp.json()
    iid = j.get("id")
    print(f"✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
    print(f"   {j.get('permalink','')}")
    # Add to stock_config con floor_override + ceiling_override = $149
    try: cfg = json.load(open("stock_config_claribel.json"))
    except: cfg = {}
    cfg[iid] = {
        "line": "Catalog-Claribel-149",
        "label": title[:45],
        "price": PRICE,
        "base_price": PRICE,
        "catalog_product_id": CPID,
        "auto_replenish": True,
        "min_visible": 1,
        "real_stock": REAL_STOCK,
        "daily_reset_to": REAL_STOCK,
        "floor_override": PRICE,        # bot no baja de aquí
        "ceiling_override": PRICE,       # bot no sube de aquí (precio fijo)
        "active": True,
        "condition": "new",
        "type": "catalog_no_variations"
    }
    with open("stock_config_claribel.json","w") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Config: real_stock={REAL_STOCK}, floor=ceiling=${PRICE} (precio fijo)")
else:
    err = rp.json() if rp.headers.get("content-type","").startswith("application/json") else rp.text
    print(f"❌ {json.dumps(err, ensure_ascii=False)[:500]}")
