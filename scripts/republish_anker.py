"""Cerrar MLM5280672472 + crear nuevo con catalog MLM44731712 (sin Anker)."""
import os, requests, json, time
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}

# 1. Cerrar el nuevo erróneo
BAD = "MLM5280672472"
print(f"=== Cerrando {BAD} (también con Anker) ===")
r1 = requests.put(f"https://api.mercadolibre.com/items/{BAD}", headers=H, json={"status":"closed"}, timeout=15)
print(f"  CLOSE: HTTP {r1.status_code}")

# 2. Get viejo (MLM2890818973) para copiar fotos/precio/etc
OLD = "MLM2890818973"
old = requests.get(f"https://api.mercadolibre.com/items/{OLD}", headers=H).json()

# 3. Crear con catalog NUEVO MLM44731712 (DM vacío - limpio)
NEW_CPID = "MLM44731712"
print(f"\n=== Verificando catalog destino {NEW_CPID} ===")
prod = requests.get(f"https://api.mercadolibre.com/products/{NEW_CPID}", headers=H).json()
print(f"  name: {prod.get('name','')[:80]}")
print(f"  status: {prod.get('status')}")
for a in prod.get("attributes", []):
    if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","COLOR"):
        print(f"  {a.get('id'):20} = {a.get('value_name')}")

new_item = {
    "category_id": old.get("category_id"),
    "price": old.get("price"),
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_pro",
    "pictures": [{"source": p.get("url")} for p in old.get("pictures",[])],
    "shipping": old.get("shipping",{}),
    "sale_terms": old.get("sale_terms",[]),
    "catalog_product_id": NEW_CPID,
    "catalog_listing": True,
}

print(f"\n=== Creando con CPID {NEW_CPID} ===")
r2 = requests.post("https://api.mercadolibre.com/items", headers=H, json=new_item, timeout=30)
print(f"POST /items: HTTP {r2.status_code}")
if r2.status_code in (200,201):
    new_data = r2.json()
    new_id = new_data.get("id")
    print(f"  ✅ Nuevo: {new_id}")
    time.sleep(3)
    # Verificar atributos
    nv = requests.get(f"https://api.mercadolibre.com/items/{new_id}", headers=H).json()
    print(f"\n=== ATRIBUTOS del nuevo {new_id} ===")
    for a in nv.get("attributes", []):
        if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","MODEL_NAME","LINE","COLOR","MAIN_COLOR"):
            print(f"  {a.get('id'):20} = {a.get('value_name')}")
    print(f"  user_product_id: {nv.get('user_product_id')}")
    print(f"  permalink: {nv.get('permalink')}")
    print(f"  status: {nv.get('status')}")
else:
    print(f"  body: {r2.text[:600]}")
