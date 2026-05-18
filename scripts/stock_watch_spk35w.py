import os, requests, json
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token","client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}
print("=== Audifonos MLM2940664057 ===")
item = requests.get("https://api.mercadolibre.com/items/MLM2940664057", headers=h, timeout=20).json()
print("title:", item.get("title"))
print("status:", item.get("status"))
print("price:", item.get("price"))
print("qty:", item.get("available_quantity"))
print("sold:", item.get("sold_quantity"))
print("perma:", item.get("permalink"))
sh = item.get("shipping") or {}
print("shipping:", sh.get("logistic_type"), "free:", sh.get("free_shipping"))
print("=== Top 5 pics ===")
for i, p in enumerate(item.get("pictures", [])[:5]):
    print(f"  pic{i}: {p.get('secure_url')}")
