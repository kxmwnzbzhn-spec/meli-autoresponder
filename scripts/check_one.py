import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_MAYRELY={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
sid="MLM5411409288"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
print(f"status={g.get('status')}  sub_status={g.get('sub_status')}  health={g.get('health')}")
print(f"price=${g.get('price')}  qty={g.get('available_quantity')}")
print(f"title='{g.get('title')}'")
print(f"permalink={g.get('permalink')}")
print(f"date_created={g.get('date_created')}")
print(f"last_updated={g.get('last_updated')}")
print(f"buying_mode={g.get('buying_mode')}  listing_type={g.get('listing_type_id')}")
print(f"catalog_listing={g.get('catalog_listing')}  cpid={g.get('catalog_product_id')}")
print(f"category_id={g.get('category_id')}")
print(f"shipping={g.get('shipping')}")
print(f"pictures_count={len(g.get('pictures') or [])}")
# health/validation issues
r2=requests.get(f"{API}/items/{sid}/health/actions",headers=H,timeout=20).json()
print(f"\nhealth/actions: {r2}")
# under_review reasons
r3=requests.get(f"{API}/items/{sid}/health",headers=H,timeout=20)
print(f"\nhealth: {r3.status_code} {r3.text[:600]}")
