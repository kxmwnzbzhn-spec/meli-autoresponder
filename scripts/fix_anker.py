import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
UP_ID = "MLMU3928750610"

# 1. GET el user_product
print("=== GET user_product ===")
up = requests.get(f"https://api.mercadolibre.com/user-products/{UP_ID}", headers=H, timeout=10).json()
print(f"  status: {up.get('status','?')}")
print(f"  attrs (DETAILED_MODEL):")
for a in up.get("attributes", []):
    if a.get("id") == "DETAILED_MODEL":
        print(f"    value_name={a.get('value_name')} value_id={a.get('value_id')}")

# 2. PUT con DETAILED_MODEL corregido
print("\n=== PUT user_product DETAILED_MODEL=JBLGO4 ===")
new_attrs = []
for a in up.get("attributes", []):
    if a.get("id") == "DETAILED_MODEL":
        new_attrs.append({"id":"DETAILED_MODEL", "value_name":"JBLGO4", "value_id": None})
    else:
        new_attrs.append(a)
r1 = requests.put(f"https://api.mercadolibre.com/user-products/{UP_ID}", headers=H,
                  json={"attributes": new_attrs}, timeout=20)
print(f"  HTTP {r1.status_code}: {r1.text[:400]}")

# 3. Verificar
up2 = requests.get(f"https://api.mercadolibre.com/user-products/{UP_ID}", headers=H, timeout=10).json()
for a in up2.get("attributes", []):
    if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","LINE","MODEL_NAME"):
        print(f"  {a.get('id'):20} = {a.get('value_name')} (id={a.get('value_id')})")

# 4. Esperar 5s y check item
import time; time.sleep(5)
print("\n=== Item después ===")
item = requests.get(f"https://api.mercadolibre.com/items/MLM2890818973", headers=H).json()
for a in item.get("attributes", []):
    if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","LINE","MODEL_NAME"):
        print(f"  {a.get('id'):20} = {a.get('value_name')} (id={a.get('value_id')})")
