import os, requests, json, sys
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")  # Juan

CPID = "MLM44710367"
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
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})")

# Build catalog listing payload
payload = {
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
    "shipping": {
        "mode": "me2",
        "free_shipping": False,
        "tags": ["self_service_in"]
    }
}

print("\nPOST /items con catalog_listing=true...")
print(json.dumps(payload, indent=2, ensure_ascii=False))

r = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
print(f"\n→ {r.status_code}")
try:
    j = r.json()
    print(json.dumps(j, indent=2, ensure_ascii=False)[:2500])
except:
    print(r.text[:2000])

if r.status_code in (200, 201):
    iid = r.json().get("id")
    print(f"\n✅ Publicada: {iid}")
    print(f"   Permalink: {r.json().get('permalink','')}")
