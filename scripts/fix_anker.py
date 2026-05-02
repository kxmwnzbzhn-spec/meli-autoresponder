import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
IID = "MLM2890818973"
UP = "MLMU3928750610"
SELLER = 2681696373

# Probar varios endpoints para user_product
for path in [
    f"/users/{SELLER}/user_products/{UP}",
    f"/users/{SELLER}/user-products/{UP}",
    f"/sites/MLM/user_products/{UP}",
    f"/user_products/{UP}",  # underscore not dash
]:
    r = requests.get(f"https://api.mercadolibre.com{path}", headers=H, timeout=10)
    print(f"GET {path[-60:]} → {r.status_code} {r.text[:150]}")

# Probar detach: set user_product_id=null en el item
print("\n=== Approach: PUT item con user_product_id=null ===")
r = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
                  json={"user_product_id": None}, timeout=15)
print(f"  HTTP {r.status_code}: {r.text[:300]}")

import time; time.sleep(3)
# Si se detached, ahora actualizar attributes
item = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
print(f"\n  user_product_id ahora: {item.get('user_product_id')}")
if not item.get('user_product_id'):
    print("\n=== Detached! Ahora actualizando DETAILED_MODEL ===")
    r2 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
        json={"attributes":[{"id":"DETAILED_MODEL", "value_name":"JBLGO4"}]}, timeout=15)
    print(f"  HTTP {r2.status_code}: {r2.text[:200]}")
    item3 = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
    for a in item3.get("attributes", []):
        if a.get("id") in ("DETAILED_MODEL","BRAND","MODEL"):
            print(f"  {a.get('id'):20} = {a.get('value_name')} (id={a.get('value_id')})")
