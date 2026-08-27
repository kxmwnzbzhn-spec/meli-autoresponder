#!/usr/bin/env python3
"""Clone one Mercado Libre catalog listing from Edilberto to Jorge Luis.

Safety properties:
- accepts exactly one source item per run;
- verifies the source and target seller IDs;
- requires a catalog product;
- always publishes/reuses the target in condition new;
- never changes the source listing;
- verifies the destination before reporting success.
"""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_SELLER = 3616975257
TARGET_SELLER = 3640697853
TIMEOUT = 30

raw_id = os.environ["SOURCE_ITEM_ID"].strip().upper().replace("-", "")
SOURCE_ID = raw_id if raw_id.startswith("MLM") else f"MLM{raw_id}"
CID = os.environ["MELI_APP_ID_NEW"]
CSECRET = os.environ["MELI_APP_SECRET_NEW"]


def refresh(secret_name, output_path):
    response = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CID,
            "client_secret": CSECRET,
            "refresh_token": os.environ[secret_name],
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    with open(output_path, "w") as handle:
        handle.write(data.get("refresh_token", ""))
    return data["access_token"]


source_token = refresh(
    "MELI_REFRESH_TOKEN_EDILBERTO", "/tmp/edilberto_rotated_token"
)
target_token = refresh(
    "MELI_REFRESH_TOKEN_JORGE_LUIS", "/tmp/jorge_luis_rotated_token"
)
HS = {"Authorization": f"Bearer {source_token}"}
HT = {"Authorization": f"Bearer {target_token}"}
HTJ = {**HT, "Content-Type": "application/json"}


def get_item(item_id, headers, seller_id):
    response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != seller_id:
        raise RuntimeError(
            f"{item_id}: seller={item.get('seller_id')} esperado={seller_id}"
        )
    return item


def valid_gtin(item):
    for attribute in item.get("attributes") or []:
        if attribute.get("id") not in {"GTIN", "EAN", "UPC"}:
            continue
        value = str(attribute.get("value_name") or "").strip()
        if value.isdigit() and 8 <= len(value) <= 14:
            return value
    return None


def target_items():
    offset = 0
    while offset < 2000:
        response = requests.get(
            f"{API}/users/{TARGET_SELLER}/items/search",
            headers=HT,
            params={"limit": 100, "offset": offset},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        ids = response.json().get("results") or []
        yield from ids
        if len(ids) < 100:
            break
        offset += 100


def find_existing(catalog_product_id):
    for item_id in target_items():
        try:
            item = get_item(item_id, HT, TARGET_SELLER)
        except Exception:
            continue
        if (
            item.get("catalog_product_id") == catalog_product_id
            and bool(item.get("catalog_listing"))
            and not item.get("deleted")
        ):
            return item
    return None


source = get_item(SOURCE_ID, HS, SOURCE_SELLER)
catalog_product_id = source.get("catalog_product_id")
if not catalog_product_id:
    raise RuntimeError(
        f"{SOURCE_ID}: no tiene catalog_product_id; se abortó para no publicar fuera de catálogo"
    )

print(
    f"SOURCE id={SOURCE_ID} title={source.get('title')} price={source.get('price')} "
    f"condition={source.get('condition')} catalog={catalog_product_id}",
    flush=True,
)

existing = find_existing(catalog_product_id)
target_id = existing.get("id") if existing else None
action = "reused"
if existing and existing.get("condition") != "new":
    raise RuntimeError(
        f"{target_id}: catálogo ya existe en Jorge con condition={existing.get('condition')}; "
        "se abortó sin duplicar ni modificar"
    )
if existing and existing.get("status") not in {"active", "paused"}:
    raise RuntimeError(
        f"{target_id}: catálogo ya existe en Jorge con status={existing.get('status')}; "
        "se abortó sin duplicar ni modificar"
    )
if target_id:
    response = requests.put(
        f"{API}/items/{target_id}",
        headers=HTJ,
        json={
            "price": source.get("price"),
            "available_quantity": 1,
            "status": "active",
        },
        timeout=TIMEOUT,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{target_id}: no se pudo activar {response.status_code} {response.text[:800]}"
        )
else:
    attributes = [{"id": "ITEM_CONDITION", "value_name": "Nuevo"}]
    gtin = valid_gtin(source)
    if gtin:
        attributes.insert(0, {"id": "GTIN", "value_name": gtin})

    payload = {
        "site_id": "MLM",
        "family_name": (
            source.get("family_name") or source.get("title") or "Producto"
        )[:60],
        "category_id": source.get("category_id"),
        "price": source.get("price"),
        "currency_id": source.get("currency_id") or "MXN",
        "available_quantity": 1,
        "buying_mode": source.get("buying_mode") or "buy_it_now",
        "listing_type_id": source.get("listing_type_id") or "gold_special",
        "condition": "new",
        "catalog_product_id": catalog_product_id,
        "catalog_listing": True,
        "attributes": attributes,
        "shipping": {
            "mode": "me2",
            "local_pick_up": False,
            "free_shipping": bool(
                (source.get("shipping") or {}).get("free_shipping")
            ),
        },
    }
    response = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=45)
    print(
        f"CATALOG_POST source={SOURCE_ID} HTTP={response.status_code} "
        f"BODY={response.text[:1000]}",
        flush=True,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{SOURCE_ID}: publicación falló {response.status_code} "
            f"{response.text[:1400]}"
        )
    target_id = response.json().get("id")
    if not target_id:
        raise RuntimeError(f"{SOURCE_ID}: Mercado Libre no devolvió target_id")
    action = "created"

    description_response = requests.get(
        f"{API}/items/{SOURCE_ID}/description", headers=HS, timeout=TIMEOUT
    )
    description = (
        description_response.json().get("plain_text")
        if description_response.status_code == 200
        else ""
    )
    if description:
        requests.post(
            f"{API}/items/{target_id}/description",
            headers=HTJ,
            json={"plain_text": description[:5000]},
            timeout=TIMEOUT,
        )

target = get_item(target_id, HT, TARGET_SELLER)
checks = {
    "active": target.get("status") == "active",
    "quantity_one": int(target.get("available_quantity") or 0) == 1,
    "new": target.get("condition") == "new",
    "catalog": bool(target.get("catalog_listing")),
    "same_catalog_product": target.get("catalog_product_id") == catalog_product_id,
}
if not all(checks.values()):
    raise RuntimeError(
        f"{target_id}: verificación falló checks={checks} "
        f"status={target.get('status')} qty={target.get('available_quantity')} "
        f"condition={target.get('condition')} catalog={target.get('catalog_product_id')}"
    )

result = {
    "source_id": SOURCE_ID,
    "target_id": target_id,
    "action": action,
    "title": target.get("title"),
    "price": target.get("price"),
    "condition": target.get("condition"),
    "status": target.get("status"),
    "quantity": target.get("available_quantity"),
    "catalog_product_id": target.get("catalog_product_id"),
    "catalog_listing": target.get("catalog_listing"),
    "permalink": target.get("permalink"),
}
with open("/tmp/edilberto_to_jorge_result.json", "w") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
print("CLONE_RESULT=" + json.dumps(result, ensure_ascii=False), flush=True)
