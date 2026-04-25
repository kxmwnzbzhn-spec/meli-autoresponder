import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")  # Juan

CATALOGS = ["MLM44710367", "MLM44710313", "MLM61262890"]
PRICE = 499.0
QTY = 15

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
if r.status_code != 200:
    print("token err", r.status_code, r.text); sys.exit(1)
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

results = {}
for CPID in CATALOGS:
    print(f"=== {CPID} ===")
    p = requests.get(f"https://api.mercadolibre.com/products/{CPID}", headers=H).json()
    title = p.get("name","")
    cat = p.get("category_id") or ""
    domain = p.get("domain_id","")
    print(f"  '{title[:70]}'")
    print(f"  cat={cat} domain={domain}")
    
    # If no category in product, try domain → category mapping
    if not cat and domain:
        # try to resolve via /catalog_listings/products/{cpid}/categories or product attributes
        # Common case: Bocina = MLM59800
        if domain == "MLM-SPEAKERS":
            cat = "MLM59800"
        else:
            # fetch from catalog API
            r2 = requests.get(f"https://api.mercadolibre.com/products/{CPID}/items", headers=H).json()
            if r2.get("results"):
                ref_iid = r2["results"][0].get("item_id")
                ri = requests.get(f"https://api.mercadolibre.com/items/{ref_iid}", headers=H).json()
                cat = ri.get("category_id","")
        print(f"  resolved cat → {cat}")
    
    payload = {
        "title": title[:60],
        "category_id": cat,
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
            print(f"  ❌ {json.dumps(j, ensure_ascii=False)[:600]}")
    except:
        print(f"  raw: {r.text[:500]}")
    time.sleep(2)

print(f"\nRESULTS: {json.dumps(results, indent=2)}")
# Save mapping for daily replenish
with open("juan_daily_replenish.json","w") as f:
    json.dump({"items": results, "qty_per_day": QTY}, f, indent=2)
print("Saved juan_daily_replenish.json")
