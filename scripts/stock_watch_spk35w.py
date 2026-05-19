import os, requests
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}
r = requests.get("https://api.mercadolibre.com/items/MLM2940664057", headers=h, timeout=20).json()
print(f"=== Redmi Audífonos MLM2940664057 ===")
print(f"title: {r.get('title')}")
print(f"status: {r.get('status')} | price: ${r.get('price')} | qty: {r.get('available_quantity')} | sold: {r.get('sold_quantity')}")
print(f"last_updated: {r.get('last_updated')}")
print(f"perma: {r.get('permalink')}")
