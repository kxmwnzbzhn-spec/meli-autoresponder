import os, requests, json

tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
access = tok["access_token"]
h = {"Authorization": f"Bearer {access}"}
hj = {**h, "Content-Type": "application/json"}

# Verificar seller_id antes de cualquier cambio (regla dura)
print("=== Pre-check: verificar ownership del listing ===")
r = requests.get("https://api.mercadolibre.com/items/MLM5356938548", headers=h, timeout=15).json()
print(f"  ID:          {r.get('id')}")
print(f"  Seller ID:   {r.get('seller_id')}")
print(f"  Title:       {r.get('title')[:60]}")
print(f"  Current $:   ${r.get('price')}")
print(f"  free_ship:   {r.get('shipping',{}).get('free_shipping')}")
print(f"  logistic:    {r.get('shipping',{}).get('logistic_type')}")
print(f"  Stock:       {r.get('available_quantity')}")

if r.get("seller_id") != 1668713481:
    print(f"\n✗ ABORT: seller_id mismatch. Expected 1668713481, got {r.get('seller_id')}")
    exit(1)

# Update price + free shipping
print(f"\n=== Update: precio $599 → $299 + envío gratis ===")
update = {
    "price": 299,
    "shipping": {
        "mode": "me2",
        "free_shipping": True,
        "logistic_type": "xd_drop_off"
    }
}
r2 = requests.put("https://api.mercadolibre.com/items/MLM5356938548", headers=hj, json=update, timeout=20)
print(f"  HTTP {r2.status_code}")
if r2.status_code in (200, 201):
    data = r2.json()
    print(f"  ✓ Nuevo precio: ${data.get('price')}")
    print(f"  ✓ Free shipping: {data.get('shipping',{}).get('free_shipping')}")
    print(f"  ✓ Updated at:   {data.get('last_updated')}")
else:
    print(f"  ✗ Error: {r2.text[:400]}")

# Verificación final
print(f"\n=== Verificación final ===")
r3 = requests.get("https://api.mercadolibre.com/items/MLM5356938548", headers=h, timeout=15).json()
print(f"  Precio:         ${r3.get('price')}")
print(f"  free_shipping:  {r3.get('shipping',{}).get('free_shipping')}")
print(f"  URL pública:    {r3.get('permalink')}")
