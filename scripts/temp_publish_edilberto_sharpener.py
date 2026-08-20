import json
import os
import sys
import time
import requests

API = "https://api.mercadolibre.com"
SOURCE_ID = "MLM5873427170"
SELLER_ID = 3616975257

def fail(message, response=None):
    print("ERROR:", message)
    if response is not None:
        print("HTTP", response.status_code)
        print(response.text[:12000])
    sys.exit(1)

app_id = os.environ["MELI_APP_ID"]
app_secret = os.environ["MELI_APP_SECRET"]
refresh_token = os.environ["MELI_REFRESH_TOKEN"]

token_response = requests.post(
    API + "/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "refresh_token": refresh_token,
    },
    timeout=30,
)
if not token_response.ok:
    fail("No se pudo renovar el token de Edilberto", token_response)
tokens = token_response.json()
access_token = tokens["access_token"]
rotated_token = tokens.get("refresh_token")
if rotated_token:
    with open("/tmp/edilberto_publish_rt", "w", encoding="utf-8") as handle:
        handle.write(rotated_token)

headers = {"Authorization": "Bearer " + access_token}

me_response = requests.get(API + "/users/me", headers=headers, timeout=30)
if not me_response.ok:
    fail("No se pudo identificar la cuenta", me_response)
me = me_response.json()
if int(me["id"]) != SELLER_ID:
    fail("El token no pertenece a Edilberto. seller_id=" + str(me.get("id")))
print("ACCOUNT", json.dumps({"id": me["id"], "nickname": me.get("nickname")}, ensure_ascii=False))

source_response = requests.get(API + "/items/" + SOURCE_ID, headers=headers, timeout=30)
if not source_response.ok:
    fail("No se pudo consultar la publicación original", source_response)
source = source_response.json()
source_price = source["price"]
source_catalog = source.get("catalog_product_id")
print("SOURCE", json.dumps({
    "id": source["id"],
    "title": source.get("title"),
    "price": source_price,
    "currency_id": source.get("currency_id"),
    "category_id": source.get("category_id"),
    "catalog_product_id": source_catalog,
    "listing_type_id": source.get("listing_type_id"),
    "condition": source.get("condition"),
    "permalink": source.get("permalink"),
}, ensure_ascii=False))

def seller_item_ids(status):
    response = requests.get(
        API + f"/users/{SELLER_ID}/items/search",
        headers=headers,
        params={"status": status, "limit": 100},
        timeout=30,
    )
    if not response.ok:
        return []
    return response.json().get("results", [])

existing = None
for status in ("active", "paused"):
    ids = seller_item_ids(status)
    for start in range(0, len(ids), 20):
        part = ids[start:start + 20]
        multi = requests.get(
            API + "/items",
            headers=headers,
            params={"ids": ",".join(part), "attributes": "id,title,catalog_product_id,status,price,available_quantity,permalink"},
            timeout=30,
        )
        if not multi.ok:
            continue
        for entry in multi.json():
            body = entry.get("body", {})
            same_catalog = bool(source_catalog and body.get("catalog_product_id") == source_catalog)
            same_title = body.get("title") == source.get("title") and body.get("id") != SOURCE_ID
            if same_catalog or (not source_catalog and same_title):
                existing = body
                break
        if existing:
            break
    if existing:
        break

if existing:
    update = {"price": source_price, "available_quantity": 1}
    if existing.get("status") == "paused":
        update["status"] = "active"
    update_response = requests.put(
        API + "/items/" + existing["id"],
        headers={**headers, "Content-Type": "application/json"},
        json=update,
        timeout=30,
    )
    if not update_response.ok:
        fail("El producto ya existía pero no pudo dejarse activo con 1 pieza y el precio indicado", update_response)
    item_id = existing["id"]
    print("REUSED_EXISTING", item_id)
else:
    ignored_attributes = {
        "SELLER_SKU", "SELLER_PACKAGE_HEIGHT", "SELLER_PACKAGE_LENGTH",
        "SELLER_PACKAGE_WEIGHT", "SELLER_PACKAGE_WIDTH", "PACKAGE_HEIGHT",
        "PACKAGE_LENGTH", "PACKAGE_WEIGHT", "PACKAGE_WIDTH"
    }
    attributes = []
    for attribute in source.get("attributes", []):
        attr_id = attribute.get("id")
        if not attr_id or attr_id in ignored_attributes:
            continue
        cleaned = {"id": attr_id}
        if attribute.get("value_id") is not None:
            cleaned["value_id"] = attribute["value_id"]
        elif attribute.get("value_name") is not None:
            cleaned["value_name"] = attribute["value_name"]
        else:
            continue
        attributes.append(cleaned)

    sale_terms = []
    for term in source.get("sale_terms", []):
        if not term.get("id"):
            continue
        cleaned = {"id": term["id"]}
        if term.get("value_id") is not None:
            cleaned["value_id"] = term["value_id"]
        elif term.get("value_name") is not None:
            cleaned["value_name"] = term["value_name"]
        else:
            continue
        sale_terms.append(cleaned)

    pictures = []
    for picture in source.get("pictures", []):
        picture_url = picture.get("secure_url") or picture.get("url")
        if picture_url:
            pictures.append({"source": picture_url})

    source_shipping = source.get("shipping") or {}
    shipping = {
        "mode": source_shipping.get("mode") or "me2",
        "local_pick_up": bool(source_shipping.get("local_pick_up", False)),
        "free_shipping": bool(source_shipping.get("free_shipping", False)),
    }

    payload = {
        "title": source["title"],
        "category_id": source["category_id"],
        "price": source_price,
        "currency_id": source.get("currency_id", "MXN"),
        "available_quantity": 1,
        "buying_mode": source.get("buying_mode", "buy_it_now"),
        "condition": source.get("condition", "new"),
        "listing_type_id": source.get("listing_type_id", "gold_special"),
        "pictures": pictures,
        "attributes": attributes,
        "shipping": shipping,
    }
    if sale_terms:
        payload["sale_terms"] = sale_terms
    if source_catalog:
        payload["catalog_product_id"] = source_catalog

    print("CREATE_PAYLOAD_SUMMARY", json.dumps({
        "title": payload["title"],
        "price": payload["price"],
        "quantity": payload["available_quantity"],
        "catalog_product_id": payload.get("catalog_product_id"),
        "listing_type_id": payload["listing_type_id"],
        "picture_count": len(pictures),
        "attribute_count": len(attributes),
    }, ensure_ascii=False))

    create_response = requests.post(
        API + "/items",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if not create_response.ok:
        fail("Mercado Libre rechazó la creación de la publicación", create_response)
    created = create_response.json()
    item_id = created["id"]
    print("CREATED", item_id)

    description_response = requests.get(API + "/items/" + SOURCE_ID + "/description", headers=headers, timeout=30)
    if description_response.ok:
        description = description_response.json()
        description_payload = None
        if description.get("plain_text"):
            description_payload = {"plain_text": description["plain_text"]}
        elif description.get("text"):
            description_payload = {"plain_text": description["text"]}
        if description_payload:
            add_description = requests.post(
                API + "/items/" + item_id + "/description",
                headers={**headers, "Content-Type": "application/json"},
                json=description_payload,
                timeout=30,
            )
            print("DESCRIPTION_HTTP", add_description.status_code)

time.sleep(3)
verify_response = requests.get(API + "/items/" + item_id, headers=headers, timeout=30)
if not verify_response.ok:
    fail("La publicación fue procesada pero no se pudo verificar", verify_response)
verified = verify_response.json()

result = {
    "id": verified.get("id"),
    "seller_id": verified.get("seller_id"),
    "title": verified.get("title"),
    "price": verified.get("price"),
    "currency_id": verified.get("currency_id"),
    "available_quantity": verified.get("available_quantity"),
    "status": verified.get("status"),
    "sub_status": verified.get("sub_status"),
    "catalog_product_id": verified.get("catalog_product_id"),
    "permalink": verified.get("permalink"),
}
print("PUBLISHED_RESULT", json.dumps(result, ensure_ascii=False))

if int(verified.get("seller_id", 0)) != SELLER_ID:
    fail("La publicación no quedó en la cuenta de Edilberto")
if float(verified.get("price", -1)) != float(source_price):
    fail("El precio final no coincide con la publicación original")
if int(verified.get("available_quantity", -1)) != 1:
    fail("La cantidad final no es 1")
