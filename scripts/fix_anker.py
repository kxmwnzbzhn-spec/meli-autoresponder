import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
IID = "MLM2890818973"

# Buscar el value_id correcto para "JBLGO4" o "Go 4" en el atributo DETAILED_MODEL de la categoría
# 1. Get attribute spec
print("=== GET MLM59800 attributes ===")
attrs = requests.get(f"https://api.mercadolibre.com/categories/MLM59800/attributes", headers=H).json()
dm_attr = next((a for a in attrs if a.get("id") == "DETAILED_MODEL"), None)
if dm_attr:
    print(f"  DETAILED_MODEL: {dm_attr.get('value_type')}")
    vals = dm_attr.get("values", [])
    print(f"  values count: {len(vals)}")
    # Buscar JBLGO4 o relacionados
    for v in vals:
        if "GO4" in (v.get("name","") or "").upper() or "GO 4" in (v.get("name","") or "").upper() or "JBL" in (v.get("name","") or "").upper():
            print(f"    id={v.get('id')} name={v.get('name')}")

# 2. Si DETAILED_MODEL es value_type 'string' open, pasar value_name solo
# 3. Probar sin id solo name
print("\n=== Approach: send DETAILED_MODEL como only-name (sin id) ===")
r1 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
    json={"attributes":[{"id":"DETAILED_MODEL", "value_name":"JBLGO4"}]}, timeout=15)
print(f"  HTTP {r1.status_code}: {r1.text[:200]}")

import time; time.sleep(3)
item = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
for a in item.get("attributes", []):
    if a.get("id") == "DETAILED_MODEL":
        print(f"  DESPUÉS: {a.get('value_name')} (id={a.get('value_id')})")

# 4. Como último intento: enviar attribute con values=[] para borrar
if "Anker" in str(item):
    print("\n=== Approach: deletar attribute via 'values':[] ===")
    r3 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
        json={"attributes":[{"id":"DETAILED_MODEL", "values":[{"name":"JBLGO4"}]}]}, timeout=15)
    print(f"  HTTP {r3.status_code}: {r3.text[:200]}")
    item2 = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
    for a in item2.get("attributes", []):
        if a.get("id") == "DETAILED_MODEL":
            print(f"  DESPUÉS v2: {a.get('value_name')} (id={a.get('value_id')})")
