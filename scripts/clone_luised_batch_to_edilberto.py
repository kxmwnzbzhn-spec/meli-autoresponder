#!/usr/bin/env python3
"""Clona tres publicaciones autorizadas de Luis Eduardo a Edilberto.

Crea/reutiliza una oferta de catálogo por producto, conserva precio y condición,
y deja exactamente una unidad visible. No modifica las publicaciones fuente.
"""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_IDS = ["MLM3356015807", "MLM3356017195", "MLM3355976643", "MLM3356015233"]
SOURCE_SELLER = 3584846108
TARGET_SELLER = 3616975257
TIMEOUT = 30

CID = os.environ["MELI_APP_ID_NEW"]
CSECRET = os.environ["MELI_APP_SECRET_NEW"]


def refresh(secret_name, out_path):
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
    with open(out_path, "w") as handle:
        handle.write(data.get("refresh_token", ""))
    return data["access_token"]


source_token = refresh("MELI_REFRESH_TOKEN_LUISED", "/tmp/luised_rotated_token")
target_token = refresh("MELI_REFRESH_TOKEN_EDILBERTO", "/tmp/edilberto_rotated_token")
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


def valid_gtin(source):
    for attribute in source.get("attributes") or []:
        if attribute.get("id") not in {"GTIN", "EAN", "UPC"}:
            continue
        value = str(attribute.get("value_name") or "").strip()
        if value.isdigit() and 8 <= len(value) <= 14:
            return value
    return None


def condition_data(source):
    condition = source.get("condition") or "new"
    if condition == "refurbished":
        return condition, "Reacondicionado"
    if condition == "used":
        return condition, "Usado"
    return "new", "Nuevo"


def existing_target(catalog_product_id, condition):
    response = requests.get(
        f"{API}/users/{TARGET_SELLER}/items/search",
        headers=HT,
        params={"status": "active", "limit": 100},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    for item_id in response.json().get("results") or []:
        try:
            item = get_item(item_id, HT, TARGET_SELLER)
        except Exception:
            continue
        if (
            item.get("catalog_product_id") == catalog_product_id
            and item.get("condition") == condition
            and not item.get("deleted")
        ):
            return item_id
    return None


def clone_one(source):
    source_id = source["id"]
    catalog_product_id = source.get("catalog_product_id")
    if not catalog_product_id:
        raise RuntimeError(f"{source_id}: sin catalog_product_id; abortado sin publicar")

    condition, item_condition = condition_data(source)
    found = existing_target(catalog_product_id, condition)
    if found:
        updated = requests.put(
            f"{API}/items/{found}",
            headers=HTJ,
            json={"available_quantity": 1, "status": "active"},
            timeout=TIMEOUT,
        )
        if updated.status_code not in (200, 201):
            raise RuntimeError(
                f"{found}: normalización {updated.status_code} {updated.text[:600]}"
            )
        print(f"REUSED {source_id}->{found}", flush=True)
        return found, "reused"

    attributes = [{"id": "ITEM_CONDITION", "value_name": item_condition}]
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
        "condition": condition,
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
    if condition == "refurbished":
        grading = next(
            (
                a for a in (source.get("attributes") or [])
                if a.get("id") == "GRADING"
            ),
            None,
        )
        if grading:
            payload["attributes"].append({
                "id": "GRADING",
                "value_id": grading.get("value_id"),
                "value_name": grading.get("value_name"),
            })
        payload["sale_terms"] = source.get("sale_terms") or [
            {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
            {"id": "WARRANTY_TIME", "value_name": "90 días"},
        ]

    response = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=45)
    print(
        f"CATALOG_POST {source_id} HTTP={response.status_code} "
        f"BODY={response.text[:1000]}",
        flush=True,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{source_id}: catálogo falló {response.status_code} "
            f"{response.text[:1200]}"
        )
    target_id = response.json().get("id")
    if not target_id:
        raise RuntimeError(f"{source_id}: respuesta sin target_id")

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
    print(f"CREATED {source_id}->{target_id}", flush=True)
    return target_id, "created"


def verify(target_id):
    item = get_item(target_id, HT, TARGET_SELLER)
    if item.get("status") != "active" or int(item.get("available_quantity") or 0) != 1:
        updated = requests.put(
            f"{API}/items/{target_id}",
            headers=HTJ,
            json={"available_quantity": 1, "status": "active"},
            timeout=TIMEOUT,
        )
        if updated.status_code not in (200, 201):
            raise RuntimeError(
                f"{target_id}: verificación PUT {updated.status_code} "
                f"{updated.text[:500]}"
            )
        item = get_item(target_id, HT, TARGET_SELLER)
    if item.get("status") != "active" or int(item.get("available_quantity") or 0) != 1:
        raise RuntimeError(
            f"{target_id}: status={item.get('status')} "
            f"qty={item.get('available_quantity')}"
        )
    print(
        f"VERIFIED {target_id} status=active qty=1 price={item.get('price')} "
        f"condition={item.get('condition')} title={item.get('title')}",
        flush=True,
    )
    return item


results = []
for source_id in SOURCE_IDS:
    source = get_item(source_id, HS, SOURCE_SELLER)
    print(
        f"SOURCE {source_id} status={source.get('status')} "
        f"price={source.get('price')} condition={source.get('condition')} "
        f"catalog={source.get('catalog_product_id')} title={source.get('title')}",
        flush=True,
    )
    target_id, action = clone_one(source)
    target = verify(target_id)
    results.append({
        "source_id": source_id,
        "target_id": target_id,
        "action": action,
        "title": target.get("title"),
        "price": target.get("price"),
        "condition": target.get("condition"),
        "status": target.get("status"),
        "quantity": target.get("available_quantity"),
        "user_product_id": target.get("user_product_id"),
        "catalog_product_id": target.get("catalog_product_id"),
        "permalink": target.get("permalink"),
    })

with open("/tmp/luised_batch_results.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("BATCH_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
