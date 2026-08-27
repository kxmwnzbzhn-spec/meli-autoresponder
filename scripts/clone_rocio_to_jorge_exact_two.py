#!/usr/bin/env python3
"""Clone exactly two authorized Rocio listings to Jorge Luis, idempotently."""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_IDS = ["MLM3264208209", "MLM5992432016"]
SOURCE_SELLER = 3478435727
TARGET_SELLER = 3640697853
TIMEOUT = 30


def refresh(client_id, client_secret, refresh_token, output_path):
    response = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    with open(output_path, "w") as handle:
        handle.write(data.get("refresh_token", ""))
    return data["access_token"]


source_token = refresh(
    "2008666770714005",
    os.environ["MELI_APP_SECRET"],
    os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"],
    "/tmp/rocioangel_rotated_token",
)
target_token = refresh(
    os.environ["MELI_APP_ID_NEW"],
    os.environ["MELI_APP_SECRET_NEW"],
    os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"],
    "/tmp/jorge_luis_rotated_token",
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


def target_items():
    offset = 0
    while offset < 3000:
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


def find_existing(catalog_product_id, condition):
    if not catalog_product_id:
        return None
    for item_id in target_items():
        try:
            item = get_item(item_id, HT, TARGET_SELLER)
        except Exception:
            continue
        if (
            item.get("catalog_product_id") == catalog_product_id
            and item.get("condition") == condition
            and bool(item.get("catalog_listing"))
            and not item.get("deleted")
        ):
            return item
    return None


def valid_gtin(source):
    for attribute in source.get("attributes") or []:
        if attribute.get("id") not in {"GTIN", "EAN", "UPC"}:
            continue
        value = str(attribute.get("value_name") or "").strip()
        if value.isdigit() and 8 <= len(value) <= 14:
            return value
    return None


def clone_one(source):
    source_id = source["id"]
    catalog_product_id = source.get("catalog_product_id")
    if not catalog_product_id:
        raise RuntimeError(
            f"{source_id}: no tiene producto de catálogo; se abortó para evitar una copia distinta"
        )
    condition = source.get("condition")
    if condition not in {"new", "used", "refurbished"}:
        raise RuntimeError(f"{source_id}: condición no soportada {condition}")

    existing = find_existing(catalog_product_id, condition)
    if existing:
        target_id = existing["id"]
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
                f"{target_id}: no se pudo normalizar {response.status_code} {response.text[:800]}"
            )
        return target_id, "reused"

    attrs = []
    gtin = valid_gtin(source)
    if gtin:
        attrs.append({"id": "GTIN", "value_name": gtin})
    item_condition = next(
        (
            a.get("value_name")
            for a in (source.get("attributes") or [])
            if a.get("id") == "ITEM_CONDITION" and a.get("value_name")
        ),
        {"new": "Nuevo", "used": "Usado", "refurbished": "Reacondicionado"}[condition],
    )
    attrs.append({"id": "ITEM_CONDITION", "value_name": item_condition})
    for attribute in source.get("attributes") or []:
        if attribute.get("id") == "GRADING" and attribute.get("value_name"):
            attrs.append({
                "id": "GRADING",
                "value_id": attribute.get("value_id"),
                "value_name": attribute.get("value_name"),
            })

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
        "condition": condition,
        "catalog_product_id": catalog_product_id,
        "catalog_listing": True,
        "attributes": attrs,
        "shipping": {
            "mode": "me2",
            "local_pick_up": bool((source.get("shipping") or {}).get("local_pick_up")),
            "free_shipping": bool((source.get("shipping") or {}).get("free_shipping")),
        },
    }
    sale_terms = []
    for term in source.get("sale_terms") or []:
        if term.get("id") in {"WARRANTY_TYPE", "WARRANTY_TIME"}:
            copied = {"id": term["id"]}
            if term.get("value_id"):
                copied["value_id"] = term["value_id"]
            if term.get("value_name"):
                copied["value_name"] = term["value_name"]
            sale_terms.append(copied)
    if sale_terms:
        payload["sale_terms"] = sale_terms

    response = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=45)
    print(
        f"CATALOG_POST source={source_id} HTTP={response.status_code} "
        f"BODY={response.text[:1200]}",
        flush=True,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{source_id}: publicación falló {response.status_code} {response.text[:1600]}"
        )
    target_id = response.json().get("id")
    if not target_id:
        raise RuntimeError(f"{source_id}: Mercado Libre no devolvió target_id")

    description_response = requests.get(
        f"{API}/items/{source_id}/description", headers=HS, timeout=TIMEOUT
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
    return target_id, "created"


results = []
for source_id in SOURCE_IDS:
    source = get_item(source_id, HS, SOURCE_SELLER)
    print(
        f"SOURCE id={source_id} title={source.get('title')} price={source.get('price')} "
        f"condition={source.get('condition')} catalog={source.get('catalog_product_id')}",
        flush=True,
    )
    target_id, action = clone_one(source)
    target = get_item(target_id, HT, TARGET_SELLER)
    checks = {
        "active": target.get("status") == "active",
        "quantity_one": int(target.get("available_quantity") or 0) == 1,
        "same_price": float(target.get("price") or 0) == float(source.get("price") or 0),
        "same_condition": target.get("condition") == source.get("condition"),
        "catalog": bool(target.get("catalog_listing")),
        "same_catalog_product": (
            target.get("catalog_product_id") == source.get("catalog_product_id")
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"{target_id}: verificación falló checks={checks} "
            f"source_title={source.get('title')} target_title={target.get('title')}"
        )
    results.append({
        "source_id": source_id,
        "target_id": target_id,
        "action": action,
        "source_title": source.get("title"),
        "target_title": target.get("title"),
        "price": target.get("price"),
        "condition": target.get("condition"),
        "status": target.get("status"),
        "quantity": target.get("available_quantity"),
        "catalog_product_id": target.get("catalog_product_id"),
        "permalink": target.get("permalink"),
    })

with open("/tmp/rocio_to_jorge_exact_results.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("CLONE_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
