import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
IID = "MLM2890818973"

# Ver el detalle completo del attribute Anker
item = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
for a in item.get("attributes", []):
    if a.get("id") == "DETAILED_MODEL":
        print(f"DETAILED_MODEL completo: {json.dumps(a, indent=2, ensure_ascii=False)}")
        break

# Probar varios approaches para borrar/cambiar
print("\n=== Approach 1: value_id=None + value_name=JBLGO4 ===")
r1 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
    json={"attributes":[{"id":"DETAILED_MODEL", "value_id": None, "value_name": "JBLGO4"}]}, timeout=15)
print(f"  HTTP {r1.status_code}: {r1.text[:300]}")
item2 = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
for a in item2.get("attributes", []):
    if a.get("id") == "DETAILED_MODEL":
        print(f"  AHORA: value_name={a.get('value_name')} value_id={a.get('value_id')}")

if "Anker" in str(item2):
    print("\n=== Approach 2: value_id explícito '' (string vacío) ===")
    r2 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
        json={"attributes":[{"id":"DETAILED_MODEL", "value_id": "", "value_name": "JBLGO4"}]}, timeout=15)
    print(f"  HTTP {r2.status_code}: {r2.text[:300]}")

# Final check
item3 = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
print(f"\n=== ESTADO FINAL ===")
for a in item3.get("attributes", []):
    aid = a.get("id")
    if aid in ("BRAND","MODEL","DETAILED_MODEL","LINE","MANUFACTURER","MODEL_NAME"):
        print(f"  {aid:20} = {a.get('value_name')} (id={a.get('value_id')})")
