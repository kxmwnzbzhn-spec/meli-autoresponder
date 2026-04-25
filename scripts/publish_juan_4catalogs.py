import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")  # Juan

CATALOGS = ["MLM44710367", "MLM44710313", "MLM61262890", "MLM37361021"]
PRICE = 499.0
QTY = 15
# All 4 are JBL Go 4 = Bocinas Bluetooth
CATEGORY = "MLM59800"

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

# Load existing mapping
existing = {}
try:
    with open("juan_daily_replenish.json") as f:
        existing = json.load(f).get("items", {})
except: pass

results = dict(existing)
for CPID in CATALOGS:
    if CPID in existing and existing[CPID]:
        print(f"=== {CPID} (skip → {existing[CPID]}) ===\n")
        continue
    print(f"=== {CPID} ===")
    
    # Try minimal payload first - catalog inherits everything
    payload = {
        "category_id": CATEGORY,
        "catalog_product_id": CPID,
        "catalog_listing": True,
        "price": PRICE,
        "available_quantity": QTY,
        "currency_id": "MXN",
        "condition": "new",
        "listing_type_id": "gold_special",
        "sale_terms": [
            {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
            {"id": "WARRANTY_TIME", "value_name": "30 días"}
        ],
        "shipping": {"mode": "me2", "free_shipping": False, "tags": ["self_service_in"]}
    }
    r = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
    print(f"  POST → {r.status_code}")
    try:
        j = r.json()
        if r.status_code in (200,201):
            iid = j.get("id")
            print(f"  ✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
            print(f"     {j.get('permalink','')}")
            results[CPID] = iid
        else:
            print(f"  ❌ {json.dumps(j, ensure_ascii=False)[:1200]}")
    except:
        print(f"  raw: {r.text[:600]}")
    time.sleep(2)

print(f"\nRESULTS:\n{json.dumps(results, indent=2)}")
with open("juan_daily_replenish.json","w") as f:
    json.dump({"items": results, "qty_per_day": QTY, "price": PRICE}, f, indent=2)
