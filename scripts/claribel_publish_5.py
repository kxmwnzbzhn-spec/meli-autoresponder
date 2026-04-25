import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_CLARIBEL","")

# 4 Go 4 catalogs + Sony catalog
PUBS = [
    {"cpid":"MLM44710367","label":"Go 4 Azul"},
    {"cpid":"MLM44710313","label":"Go 4 Roja"},
    {"cpid":"MLM37361021","label":"Go 4 Camuflaje"},
    {"cpid":"MLM61262890","label":"Go 4 Celeste/Aqua"},
    {"cpid":"MLM25912333","label":"Sony SRS-XB100 Negro"},
]
PRICE_GO4 = 499.0
PRICE_SONY = 549.0
QTY = 1  # MELI visible
CATEGORY = "MLM59800"

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

results = {}
for pub in PUBS:
    CPID = pub["cpid"]
    label = pub["label"]
    price = PRICE_SONY if "sony" in label.lower() else PRICE_GO4
    
    print(f"=== {CPID} {label} ===")
    p = requests.get(f"https://api.mercadolibre.com/products/{CPID}", headers=H).json()
    title = (p.get("name") or "")[:60]
    print(f"  title: '{title}'")
    
    payload = {
        "title": title,
        "category_id": CATEGORY,
        "catalog_product_id": CPID,
        "catalog_listing": True,
        "price": price,
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
    rp = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
    print(f"  POST → {rp.status_code}")
    try:
        j = rp.json()
        if rp.status_code in (200,201):
            iid = j.get("id")
            print(f"  ✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
            print(f"     {j.get('permalink','')}")
            results[CPID] = {"iid":iid,"label":label,"price":price}
        else:
            print(f"  ❌ {json.dumps(j, ensure_ascii=False)[:600]}")
    except Exception as e:
        print(f"  raw: {rp.text[:400]} err: {e}")
    time.sleep(2)

print(f"\nRESULTS:\n{json.dumps(results, indent=2, ensure_ascii=False)}")

# Save mapping
out = {
    "items": {cpid: r["iid"] for cpid,r in results.items()},
    "labels": {r["iid"]: r["label"] for r in results.values()},
    "prices": {r["iid"]: r["price"] for r in results.values()},
    "qty_per_day": 10,
    "visible": 1,
    "reset_hours": 24
}
with open("claribel_daily_replenish.json","w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("Saved claribel_daily_replenish.json")
