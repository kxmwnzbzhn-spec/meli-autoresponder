#!/usr/bin/env python3
"""Clona dos publicaciones autorizadas de Rocío Angel hacia Edilberto.

Idempotente: reutiliza una publicación activa del mismo producto de catálogo en Edilberto.
Siempre deja el destino activo con una unidad y registra priority replenish.
"""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_IDS = ["MLM5992405574", "MLM5992432016"]
SOURCE_SELLER = 3478435727
TARGET_SELLER = 3616975257
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
    token = response.json()
    with open(output_path, "w") as handle:
        handle.write(token.get("refresh_token", ""))
    return token["access_token"]


rocio_token = refresh(
    "2008666770714005",
    os.environ["MELI_APP_SECRET"],
    os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"],
    "/tmp/rocioangel_rotated_token",
)
edilberto_token = refresh(
    os.environ["MELI_APP_ID_NEW"],
    os.environ["MELI_APP_SECRET_NEW"],
    os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    "/tmp/edilberto_rotated_token",
)
HS = {"Authorization": f"Bearer {rocio_token}"}
HT = {"Authorization": f"Bearer {edilberto_token}"}
HTJ = {**HT, "Content-Type": "application/json"}


def get_item(item_id, headers, expected_seller):
    response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != expected_seller:
        raise RuntimeError(
            f"{item_id}: seller={item.get('seller_id')} esperado={expected_seller}"
        )
    return item


def existing_target(catalog_product_id):
    if not catalog_product_id:
        return None
    response = requests.get(
        f"{API}/sites/MLM/search",
        headers=HT,
        params={"seller_id": TARGET_SELLER, "limit": 50},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    for result in response.json().get("results") or []:
        if result.get("catalog_product_id") != catalog_product_id:
            continue
        item_id = result.get("id")
        if not item_id:
            continue
        item = get_item(item_id, HT, TARGET_SELLER)
        if item.get("status") != "closed" and not item.get("deleted"):
            return item_id
    return None


def clone_one(source):
    source_id = source["id"]
    catalog_product_id = source.get("catalog_product_id")
    found = existing_target(catalog_product_id)
    if found:
        response = requests.put(
            f"{API}/items/{found}",
            headers=HTJ,
            json={"available_quantity": 1, "status": "active"},
            timeout=TIMEOUT,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"{found}: no se pudo normalizar {response.status_code} {response.text[:500]}"
            )
        print(f"REUSED {source_id}->{found}")
        return found, "reused"

    base = {
        "site_id": "MLM",
        "title": (source.get("title") or "Producto")[:60],
        "category_id": source.get("category_id"),
        "price": source.get("price"),
        "currency_id": source.get("currency_id") or "MXN",
        "available_quantity": 1,
        "buying_mode": source.get("buying_mode") or "buy_it_now",
        "listing_type_id": source.get("listing_type_id") or "gold_special",
        "condition": source.get("condition") or "new",
    }
    if catalog_product_id:
        payload = {
            **base,
            "catalog_product_id": catalog_product_id,
            "catalog_listing": True,
            "shipping": {
                "mode": "me2",
                "free_shipping": bool((source.get("shipping") or {}).get("free_shipping")),
            },
        }
        response = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=40)
    else:
        response = requests.Response()
        response.status_code = 400
        response._content = b'{"message":"traditional_fallback"}'

    if response.status_code not in (200, 201):
        attributes = []
        skip = {
            "SELLER_SKU", "HAZMAT_TRANSPORTABILITY", "ITEM_CONDITION",
            "PACKAGE_LENGTH", "PACKAGE_WEIGHT", "PACKAGE_WIDTH", "PACKAGE_HEIGHT",
            "SHIPMENT_PACKING", "PRODUCT_FEATURES",
        }
        for attribute in source.get("attributes") or []:
            attribute_id = attribute.get("id")
            if not attribute_id or attribute_id in skip:
                continue
            if attribute.get("value_id"):
                attributes.append({"id": attribute_id, "value_id": attribute["value_id"]})
            elif attribute.get("value_name"):
                attributes.append({"id": attribute_id, "value_name": attribute["value_name"]})
        fallback = {
            **base,
            "pictures": [
                {"source": picture.get("secure_url") or picture.get("url")}
                for picture in source.get("pictures") or []
                if picture.get("secure_url") or picture.get("url")
            ][:10],
            "attributes": attributes,
            "sale_terms": source.get("sale_terms") or [],
            "shipping": {
                "mode": "me2",
                "local_pick_up": False,
                "free_shipping": bool((source.get("shipping") or {}).get("free_shipping")),
            },
        }
        response = requests.post(f"{API}/items", headers=HTJ, json=fallback, timeout=45)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{source_id}: clone POST {response.status_code} {response.text[:1200]}"
        )
    target_id = response.json().get("id")
    if not target_id:
        raise RuntimeError(f"{source_id}: respuesta sin id")

    description_response = requests.get(
        f"{API}/items/{source_id}/description", headers=HS, timeout=TIMEOUT
    )
    if description_response.status_code == 200:
        description = description_response.json().get("plain_text") or ""
        if description:
            requests.post(
                f"{API}/items/{target_id}/description",
                headers=HTJ,
                json={"plain_text": description[:5000]},
                timeout=TIMEOUT,
            )
    print(f"CREATED {source_id}->{target_id}")
    return target_id, "created"


def verify_and_register(source, target_id):
    target = get_item(target_id, HT, TARGET_SELLER)
    if target.get("status") != "active" or int(target.get("available_quantity") or 0) != 1:
        response = requests.put(
            f"{API}/items/{target_id}",
            headers=HTJ,
            json={"available_quantity": 1, "status": "active"},
            timeout=TIMEOUT,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"{target_id}: normalización {response.status_code} {response.text[:500]}"
            )
        target = get_item(target_id, HT, TARGET_SELLER)
    if target.get("status") != "active" or int(target.get("available_quantity") or 0) != 1:
        raise RuntimeError(
            f"{target_id}: verificación status={target.get('status')} "
            f"qty={target.get('available_quantity')}"
        )

    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if sb_url and sb_key:
        headers = {
            "apikey": sb_key,
            "Authorization": f"Bearer {sb_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }
        priority = requests.post(
            f"{sb_url}/rest/v1/meli_priority_replenish",
            headers=headers,
            json={
                "item_id": target_id,
                "account": "EDILBERTO",
                "default_qty": 1,
                "product_name": (target.get("title") or source.get("title") or "")[:200],
            },
            timeout=TIMEOUT,
        )
        if priority.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"{target_id}: priority {priority.status_code} {priority.text[:500]}"
            )
    print(
        f"VERIFIED {target_id} status={target.get('status')} "
        f"qty={target.get('available_quantity')} price={target.get('price')} "
        f"title={target.get('title')}"
    )
    return target


results = []
for source_id in SOURCE_IDS:
    source = get_item(source_id, HS, SOURCE_SELLER)
    print(
        f"SOURCE {source_id} status={source.get('status')} price={source.get('price')} "
        f"catalog={source.get('catalog_product_id')} title={source.get('title')}"
    )
    target_id, action = clone_one(source)
    target = verify_and_register(source, target_id)
    results.append({
        "source_id": source_id,
        "target_id": target_id,
        "action": action,
        "status": target.get("status"),
        "quantity": target.get("available_quantity"),
        "price": target.get("price"),
        "title": target.get("title"),
        "permalink": target.get("permalink"),
    })

with open("/tmp/rocio_to_edilberto_results.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("CLONE_RESULTS=" + json.dumps(results, ensure_ascii=False))
