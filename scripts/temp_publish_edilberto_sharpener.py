import json
import os
import sys
import time
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
CATALOG_PRODUCT_ID = "MLM27222296"
TITLE = "Sacapuntas Electrico Barrilito 860"
CATEGORY_ID = "MLM167984"
SOURCE_PRICE = 1600
SOURCE_URL = "https://www.mercadolibre.com.mx/sacapuntas-electrico-barrilito-860/p/MLM27222296?pdp_filters=item_id%3AMLM5873427170"

def fail(message, response=None):
    print("ERROR:", message)
    if response is not None:
        print("HTTP", response.status_code)
        print(response.text[:12000])
    sys.exit(1)

token_response = requests.post(
    API + "/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID"],
        "client_secret": os.environ["MELI_APP_SECRET"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN"],
    },
    timeout=30,
)
if not token_response.ok:
    fail("No se pudo renovar el token de Edilberto", token_response)
tokens = token_response.json()
access_token = tokens["access_token"]
if tokens.get("refresh_token"):
    with open("/tmp/edilberto_publish_rt", "w", encoding="utf-8") as handle:
        handle.write(tokens["refresh_token"])

headers = {"Authorization": "Bearer " + access_token}
json_headers = {**headers, "Content-Type": "application/json"}

me_response = requests.get(API + "/users/me", headers=headers, timeout=30)
if not me_response.ok:
    fail("No se pudo identificar la cuenta", me_response)
me = me_response.json()
if int(me["id"]) != SELLER_ID:
    fail("El token no pertenece a Edilberto. seller_id=" + str(me.get("id")))
print("ACCOUNT", json.dumps({"id": me["id"], "nickname": me.get("nickname")}, ensure_ascii=False))
print("SOURCE", json.dumps({
    "title": TITLE,
    "price": SOURCE_PRICE,
    "currency_id": "MXN",
    "category_id": CATEGORY_ID,
    "catalog_product_id": CATALOG_PRODUCT_ID,
    "url": SOURCE_URL,
}, ensure_ascii=False))

product_response = requests.get(API + "/products/" + CATALOG_PRODUCT_ID, headers=headers, timeout=30)
product = product_response.json() if product_response.ok else {}
print("CATALOG_HTTP", product_response.status_code)

def item_ids(status):
    response = requests.get(
        API + f"/users/{SELLER_ID}/items/search",
        headers=headers,
        params={"status": status, "limit": 100},
        timeout=30,
    )
    return response.json().get("results", []) if response.ok else []

existing = None
for status in ("active", "paused"):
    ids = item_ids(status)
    for start in range(0, len(ids), 20):
        multi = requests.get(
            API + "/items",
            headers=headers,
            params={
                "ids": ",".join(ids[start:start + 20]),
                "attributes": "id,title,catalog_product_id,status,price,available_quantity,permalink",
            },
            timeout=30,
        )
        if not multi.ok:
            continue
        for entry in multi.json():
            body = entry.get("body", {})
            if body.get("catalog_product_id") == CATALOG_PRODUCT_ID:
                existing = body
                break
        if existing:
            break
    if existing:
        break

if existing:
    update = {"price": SOURCE_PRICE, "available_quantity": 1}
    if existing.get("status") == "paused":
        update["status"] = "active"
    update_response = requests.put(
        API + "/items/" + existing["id"],
        headers=json_headers,
        json=update,
        timeout=30,
    )
    if not update_response.ok:
        fail("El producto ya existía pero no pudo dejarse activo con 1 pieza y precio de $1,600", update_response)
    item_id = existing["id"]
    print("REUSED_EXISTING", item_id)
else:
    ignored = {
        "SELLER_SKU", "SELLER_PACKAGE_HEIGHT", "SELLER_PACKAGE_LENGTH",
        "SELLER_PACKAGE_WEIGHT", "SELLER_PACKAGE_WIDTH", "PACKAGE_HEIGHT",
        "PACKAGE_LENGTH", "PACKAGE_WEIGHT", "PACKAGE_WIDTH"
    }
    attributes = []
    for attribute in product.get("attributes", []):
        attr_id = attribute.get("id")
        if not attr_id or attr_id in ignored:
            continue
        cleaned = {"id": attr_id}
        if attribute.get("value_id") is not None:
            cleaned["value_id"] = attribute["value_id"]
        elif attribute.get("value_name") is not None:
            cleaned["value_name"] = attribute["value_name"]
        else:
            continue
        attributes.append(cleaned)

    pictures = []
    for picture in product.get("pictures", []):
        picture_url = picture.get("secure_url") or picture.get("url")
        if picture_url:
            pictures.append({"source": picture_url})

    payload = {
        "title": TITLE,
        "family_name": TITLE,
        "category_id": CATEGORY_ID,
        "catalog_product_id": CATALOG_PRODUCT_ID,
        "price": SOURCE_PRICE,
        "currency_id": "MXN",
        "available_quantity": 1,
        "buying_mode": "buy_it_now",
        "condition": "new",
        "listing_type_id": "gold_special",
        "shipping": {
            "mode": "me2",
            "local_pick_up": False,
            "free_shipping": True,
        },
    }
    if pictures:
        payload["pictures"] = pictures
    if attributes:
        payload["attributes"] = attributes

    print("CREATE_PAYLOAD_SUMMARY", json.dumps({
        "title": TITLE,
        "price": SOURCE_PRICE,
        "quantity": 1,
        "catalog_product_id": CATALOG_PRODUCT_ID,
        "picture_count": len(pictures),
        "attribute_count": len(attributes),
    }, ensure_ascii=False))
    create_response = requests.post(
        API + "/items",
        headers=json_headers,
        json=payload,
        timeout=60,
    )
    if not create_response.ok:
        fail("Mercado Libre rechazó la creación de la publicación", create_response)
    item_id = create_response.json()["id"]
    print("CREATED", item_id)

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
if float(verified.get("price", -1)) != float(SOURCE_PRICE):
    fail("El precio final no coincide con $1,600")
if int(verified.get("available_quantity", -1)) != 1:
    fail("La cantidad final no es 1")
