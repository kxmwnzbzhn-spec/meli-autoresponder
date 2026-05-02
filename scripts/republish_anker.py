"""Cerrar MLM2890818973 + crear nueva con DETAILED_MODEL=JBLGO4 y SIN user_product binding."""
import os, requests, json, time
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
OLD_IID = "MLM2890818973"

# 1. GET item completo + descripción
old = requests.get(f"https://api.mercadolibre.com/items/{OLD_IID}", headers=H).json()
desc = requests.get(f"https://api.mercadolibre.com/items/{OLD_IID}/description", headers=H).json()
print(f"=== Old item: {OLD_IID} ===")
print(f"  title: {old.get('title')}")
print(f"  price: ${old.get('price')}")
print(f"  CPID: {old.get('catalog_product_id')}")
print(f"  user_product_id: {old.get('user_product_id')}")
print(f"  available: {old.get('available_quantity')}")
print(f"  pictures: {len(old.get('pictures',[]))}")

# 2. Construir el nuevo item — copiar todo excepto user_product_id y arreglar DETAILED_MODEL
new_attrs = []
for a in old.get("attributes", []):
    aid = a.get("id")
    if aid == "DETAILED_MODEL":
        new_attrs.append({"id": "DETAILED_MODEL", "value_name": "JBLGO4"})
    elif aid in ("BRAND","MODEL","MANUFACTURER","LINE","MODEL_NAME","COLOR","MAIN_COLOR","ITEM_CONDITION","GTIN","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","WEIGHT","INPUT_VOLTAGE","BATTERY_LIFE","WATER_PROOF_PROTECTION","WIRELESS_TECHNOLOGY","NUMBER_OF_PIECES","TYPE","MAIN_FUNCTION","INCLUDES_BATTERIES","WITH_AUX","WITH_BLUETOOTH","WITH_USB"):
        new_attrs.append({"id":aid, "value_name": a.get("value_name"), "value_id": a.get("value_id")})

# Asegurar BRAND=JBL y MANUFACTURER=JBL
def ensure_attr(attrs, aid, vname):
    found = False
    for a in attrs:
        if a.get("id") == aid:
            a["value_name"] = vname
            a["value_id"] = None  # quitar id viejo
            found = True
    if not found:
        attrs.append({"id":aid, "value_name":vname})

ensure_attr(new_attrs, "BRAND", "JBL")
ensure_attr(new_attrs, "MANUFACTURER", "JBL")
ensure_attr(new_attrs, "MODEL", "Go 4")
ensure_attr(new_attrs, "MODEL_NAME", "Go 4")
ensure_attr(new_attrs, "DETAILED_MODEL", "JBLGO4")
ensure_attr(new_attrs, "LINE", "Go")

new_item = {
    "title": old.get("title"),
    "category_id": old.get("category_id"),
    "price": old.get("price"),
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": old.get("buying_mode","buy_it_now"),
    "condition": old.get("condition","new"),
    "listing_type_id": old.get("listing_type_id","gold_pro"),
    "pictures": [{"source": p.get("url")} for p in old.get("pictures",[])],
    "attributes": new_attrs,
    "shipping": old.get("shipping",{}),
    "sale_terms": old.get("sale_terms",[]),
}
# Quitar user_product_id explícitamente (no incluirlo)
# Quitar catalog_product_id si existe (queremos genérico)
# Pero si tiene CPID, mantenlo PERO sin user_product_id
if old.get("catalog_product_id"):
    new_item["catalog_product_id"] = old.get("catalog_product_id")
    new_item["catalog_listing"] = True

print("\n=== Creando nueva publicación ===")
print(f"  Attributes count: {len(new_attrs)}")
for a in new_attrs:
    if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","MODEL_NAME","LINE"):
        print(f"  {a['id']:20} = {a.get('value_name')}")

r1 = requests.post("https://api.mercadolibre.com/items", headers=H, json=new_item, timeout=30)
print(f"\nPOST /items: HTTP {r1.status_code}")
if r1.status_code in (200,201):
    new_data = r1.json()
    new_id = new_data.get("id")
    print(f"  ✅ Nuevo: {new_id}")

    # Copiar descripción
    if desc and desc.get("plain_text"):
        rd = requests.post(f"https://api.mercadolibre.com/items/{new_id}/description", headers=H,
                           json={"plain_text": desc.get("plain_text")}, timeout=15)
        print(f"  Description: HTTP {rd.status_code}")

    # 3. Pausar el viejo (no cerrar, para no perder shipments en proceso)
    print(f"\n=== Pausando viejo {OLD_IID} ===")
    rp = requests.put(f"https://api.mercadolibre.com/items/{OLD_IID}", headers=H,
                      json={"status":"paused"}, timeout=15)
    print(f"  PAUSE: HTTP {rp.status_code}")

    # 4. Verificar attrs nuevos
    time.sleep(3)
    new_check = requests.get(f"https://api.mercadolibre.com/items/{new_id}", headers=H).json()
    print(f"\n=== Nuevo {new_id} verificación ===")
    for a in new_check.get("attributes", []):
        if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","MODEL_NAME","LINE"):
            print(f"  {a.get('id'):20} = {a.get('value_name')} (id={a.get('value_id')})")
    print(f"  user_product_id: {new_check.get('user_product_id')}")
    print(f"  status: {new_check.get('status')}")
    print(f"  permalink: {new_check.get('permalink')}")
else:
    print(f"  body: {r1.text[:600]}")
