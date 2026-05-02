import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
IID = "MLM2890818973"

# 1. GET attributes actuales
item = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
print(f"=== {IID} ===")
print(f"Title: {item.get('title')}")
print(f"\nATRIBUTOS ACTUALES:")
for a in item.get("attributes", []):
    aid = a.get("id"); name = a.get("name",""); val = a.get("value_name","") or a.get("value_id","")
    if aid in ("BRAND","MODEL","DETAILED_MODEL","LINE","MANUFACTURER","ITEM_CONDITION","COLOR","MAIN_COLOR","MODEL_NAME"):
        print(f"  {aid:20} ({name[:30]:30}) = {val}")

# 2. Identificar cuáles necesitan fix
print("\n=== APLICANDO CORRECCIONES ===")
new_attrs = [
    {"id": "BRAND", "value_name": "JBL"},
    {"id": "MODEL", "value_name": "Go 4"},
    {"id": "DETAILED_MODEL", "value_name": "JBLGO4"},
    {"id": "LINE", "value_name": "Go"},
    {"id": "MANUFACTURER", "value_name": "JBL"},
    {"id": "MODEL_NAME", "value_name": "Go 4"},
]
rr = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H,
                  json={"attributes": new_attrs}, timeout=20)
print(f"PUT attributes: HTTP {rr.status_code}")
if rr.status_code in (200,201):
    print("✅ OK")
else:
    print(f"  body: {rr.text[:500]}")

# 3. Verificar después
item2 = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
print(f"\nATRIBUTOS DESPUÉS:")
for a in item2.get("attributes", []):
    aid = a.get("id"); val = a.get("value_name","") or a.get("value_id","")
    if aid in ("BRAND","MODEL","DETAILED_MODEL","LINE","MANUFACTURER","MODEL_NAME"):
        print(f"  {aid:20} = {val}")
