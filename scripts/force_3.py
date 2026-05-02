import os, requests, time, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}

ITEMS = [
    ("MLM2891178657", 1071),  # Grip Negra
    ("MLM2891178563", 550),   # Go 4 Rojo
    ("MLM2891178603", 614),   # Go 4 Rojo
]

print("=== STEP 1: Aplicar precio target ===")
for iid, target in ITEMS:
    r = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"price": target}, timeout=15)
    j = r.json() if r.text else {}
    print(f"  {iid} → ${target}: HTTP {r.status_code} | new_price={j.get('price','?')}")

print("\n=== STEP 2: Esperar 30s ===")
time.sleep(30)

print("\n=== STEP 3: Verificar que el precio se mantenga ===")
for iid, target in ITEMS:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    cur = item.get("price")
    status_ok = "✅ STUCK" if abs(float(cur) - target) < 1 else f"❌ REVERTIDO ${cur} (target era ${target})"
    print(f"  {iid}: ${cur}  {status_ok}")

print("\n=== STEP 4: Esperar otros 30s ===")
time.sleep(30)
for iid, target in ITEMS:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    cur = item.get("price")
    status_ok = "✅ STUCK" if abs(float(cur) - target) < 1 else f"❌ REVERTIDO ${cur}"
    print(f"  {iid}: ${cur}  {status_ok}")
