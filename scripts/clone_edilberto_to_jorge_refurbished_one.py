#!/usr/bin/env python3
"""Clone one Edilberto catalog listing to Jorge Luis as refurbished/excellent."""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_SELLER = 3616975257
TARGET_SELLER = 3640697853
TIMEOUT = 30
EXCELLENT_ID = "40108830"
PREFERRED_TARGETS = {
    "MLM3376191333": "MLM3401288599",
    "MLM6065919740": "MLM3401276511",
}

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


def grading(item):
    return next(
        (a for a in (item.get("attributes") or []) if a.get("id") == "GRADING"),
        {},
    )


def target_items(status):
    offset = 0
    while offset < 1000:
        response = requests.get(
            f"{API}/users/{TARGET_SELLER}/items/search",
            headers=HT,
            params={"status": status, "limit": 100, "offset": offset},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        ids = response.json().get("results") or []
        yield from ids
        if len(ids) < 100:
            break
        offset += 100


def find_existing(source):
    catalog_product_id = source.get("catalog_product_id")
    family_id = source.get("family_id")
    for status in ("active", "paused"):
        for item_id in target_items(status):
            try:
                item = get_item(item_id, HT, TARGET_SELLER)
            except Exception:
                continue
            item_grading = grading(item)
            is_excellent = (
                str(item_grading.get("value_id") or "") == EXCELLENT_ID
                or str(item_grading.get("value_name") or "").lower() == "excelente"
            )
            if (
                (
                    item.get("catalog_product_id") == catalog_product_id
                    or (family_id and item.get("family_id") == family_id)
                )
                and item.get("condition") == "new"
                and bool(item.get("catalog_listing"))
                and is_excellent
                and not item.get("deleted")
            ):
                return item_id
    return None


source = get_item(SOURCE_ID, HS, SOURCE_SELLER)
catalog_product_id = source.get("catalog_product_id")
if not catalog_product_id:
    raise RuntimeError(
        f"{SOURCE_ID}: no tiene catalog_product_id; abortado para no publicar fuera de catálogo"
    )

source_grading = grading(source)
print(
    f"SOURCE id={SOURCE_ID} title={source.get('title')} price={source.get('price')} "
    f"condition={source.get('condition')} grading={source_grading.get('value_name')} "
    f"catalog={catalog_product_id}",
    flush=True,
)

target_id = PREFERRED_TARGETS.get(SOURCE_ID) or find_existing(source)
action = "reused"
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
    attributes = [
        {"id": "ITEM_CONDITION", "value_name": "Reacondicionado"},
        {"id": "GRADING", "value_id": EXCELLENT_ID, "value_name": "Excelente"},
    ]
    gtin = valid_gtin(source)
    if gtin:
        attributes.insert(0, {"id": "GTIN", "value_name": gtin})

    sale_terms = list(source.get("sale_terms") or [])
    sale_terms = [
        term for term in sale_terms
        if term.get("id") != "WARRANTY_TIME" or term.get("value_name")
    ]
    term_ids = {term.get("id") for term in sale_terms}
    if "WARRANTY_TYPE" not in term_ids:
        sale_terms.append({
            "id": "WARRANTY_TYPE",
            "value_id": "2230280",
            "value_name": "Garantía del vendedor",
        })
    if "WARRANTY_TIME" not in term_ids:
        sale_terms.append({"id": "WARRANTY_TIME", "value_name": "90 días"})
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
        "sale_terms": sale_terms,
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
        f"BODY={response.text[:1200]}",
        flush=True,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{SOURCE_ID}: publicación falló {response.status_code} "
            f"{response.text[:1600]}"
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
target_grading = grading(target)
is_excellent = (
    str(target_grading.get("value_id") or "") == EXCELLENT_ID
    or str(target_grading.get("value_name") or "").lower() == "excelente"
)
checks = {
    "active": target.get("status") == "active",
    "quantity_one": int(target.get("available_quantity") or 0) == 1,
    "catalog_refurbished_mapping": target.get("condition") == "new",
    "excellent": is_excellent,
    "catalog": bool(target.get("catalog_listing")),
    "official_refurbished_title": (
        "reacondicionado" in str(target.get("title") or "").lower()
        and "excelente" in str(target.get("title") or "").lower()
    ),
}
if not all(checks.values()):
    raise RuntimeError(
        f"{target_id}: verificación falló checks={checks} "
        f"condition={target.get('condition')} grading={target_grading}"
    )

result = {
    "source_id": SOURCE_ID,
    "target_id": target_id,
    "action": action,
    "title": target.get("title"),
    "price": target.get("price"),
    "api_condition": target.get("condition"),
    "catalog_condition": "Reacondicionado - Excelente",
    "grading": target_grading.get("value_name"),
    "status": target.get("status"),
    "quantity": target.get("available_quantity"),
    "catalog_product_id": target.get("catalog_product_id"),
    "catalog_listing": target.get("catalog_listing"),
    "permalink": target.get("permalink"),
}
with open("/tmp/edilberto_to_jorge_refurb_result.json", "w") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
print("CLONE_RESULT=" + json.dumps(result, ensure_ascii=False), flush=True)
