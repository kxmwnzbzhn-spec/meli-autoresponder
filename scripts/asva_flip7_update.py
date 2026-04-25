import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_ASVA","")

# Flip 7 unificada (35w) — 4 colores
FLIP7_ITEMS = [
    "MLM5233480022",  # Negro
    "MLM5233454100",  # Azul
    "MLM2886136351",  # Morado
    "MLM2886030837",  # Rojo
]
NEW_PRICE = 199.0

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

print(f"Flip 7 ASVA → ${NEW_PRICE}, sin envío gratis\n")

for iid in FLIP7_ITEMS:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = g.get("title","")[:50]
    cur_price = g.get("price")
    cur_free = g.get("shipping",{}).get("free_shipping")
    qty = g.get("available_quantity",0)
    
    print(f"  {iid} [{title}] ${cur_price} free={cur_free} qty={qty}")
    
    # 1) Update price
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                     json={"price": NEW_PRICE})
    print(f"    price → ${NEW_PRICE} ({rp.status_code})")
    if rp.status_code != 200:
        print(f"      ❌ {rp.text[:300]}")
    time.sleep(0.5)
    
    # 2) Disable free shipping
    rs = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                     json={"shipping": {"mode": "me2", "free_shipping": False, "tags": ["self_service_in"]}})
    print(f"    free_shipping → False ({rs.status_code})")
    if rs.status_code != 200:
        print(f"      ❌ {rs.text[:400]}")
    time.sleep(1)

print("\nVerificación final:")
for iid in FLIP7_ITEMS:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    print(f"  {iid}: ${g.get('price')} free={g.get('shipping',{}).get('free_shipping')}")
print("\nDone")
