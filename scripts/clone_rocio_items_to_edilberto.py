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


def existing_target(catalog_product_id, desired_condition):
    if not catalog_product_id:
        return None
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
            and item.get("condition") == desired_condition
            and not item.get("deleted")
        ):
            return item_id
    return None


def gtin_for(source):
    for attribute in source.get("attributes") or []:
        if attribute.get("id") in {"GTIN", "EAN", "UPC"} and attribute.get("value_name"):
            return str(attribute["value_name"])
    product_id = source.get("catalog_product_id")
    if product_id:
        response = requests.get(
            f"{API}/products/{product_id}", headers=HT, timeout=TIMEOUT
        )
        if response.status_code == 200:
            for attribute in response.json().get("attributes") or []:
                if attribute.get("id") in {"GTIN", "EAN", "UPC"} and attribute.get("value_name"):
                    return str(attribute["value_name"])
    return "No aplica"


def condition_spec(source_id):
    if source_id == "MLM5992405574":
        return {
            "condition": "refurbished",
            "item_condition": "Reacondicionado",
            "family_name": "Marshall Willen II Bocina Bluetooth Caja Abierta",
            "description": (
                "Marshall Willen II en condición caja abierta. El empaque fue abierto. "
                "Producto disponible con las características indicadas en la ficha técnica "
                "y una unidad visible."
            ),
        }
    return {
        "condition": "new",
        "item_condition": "Nuevo",
        "family_name": None,
        "description": None,
    }
def clone_one(source):
    source_id = source["id"]
    catalog_product_id = source.get("catalog_product_id")
    if not catalog_product_id:
        raise RuntimeError(f"{source_id}: no tiene catalog_product_id; no se publicará fuera de catálogo")

    spec = condition_spec(source_id)
    found = existing_target(catalog_product_id, spec["condition"])
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
        return found, "reused", spec

    family_name = spec["family_name"] or source.get("family_name") or source.get("title") or "Producto"
    payload = {
        "site_id": "MLM",
        "family_name": family_name[:60],
        "category_id": source.get("category_id"),
        "price": source.get("price"),
        "currency_id": source.get("currency_id") or "MXN",
        "available_quantity": 1,
        "buying_mode": source.get("buying_mode") or "buy_it_now",
        "listing_type_id": source.get("listing_type_id") or "gold_special",
        "condition": spec["condition"],
        "catalog_product_id": catalog_product_id,
        "catalog_listing": True,
        "attributes": [
            {"id": "GTIN", "value_name": gtin_for(source)},
            {"id": "ITEM_CONDITION", "value_name": spec["item_condition"]},
        ],
        "shipping": {
            "mode": "me2",
            "local_pick_up": False,
            "free_shipping": bool((source.get("shipping") or {}).get("free_shipping")),
        },
    }
    response = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=45)
    print(f"CATALOG_POST {source_id} HTTP={response.status_code} BODY={response.text[:900]}")
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{source_id}: publicación de catálogo falló {response.status_code} "
            f"{response.text[:1200]}"
        )
    target_id = response.json().get("id")
    if not target_id:
        raise RuntimeError(f"{source_id}: respuesta sin id")

    description = spec["description"]
    if description is None:
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
    print(
        f"CREATED {source_id}->{target_id} condition={spec['condition']} "
        f"catalog_product_id={catalog_product_id}"
    )
    return target_id, "created", spec
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
    target_id, action, spec = clone_one(source)
    target = verify_and_register(source, target_id)
    if target.get("condition") != spec["condition"]:
        raise RuntimeError(
            f"{target_id}: condition={target.get('condition')} esperado={spec['condition']}"
        )
    results.append({
        "source_id": source_id,
        "target_id": target_id,
        "action": action,
        "condition": target.get("condition"),
        "status": target.get("status"),
        "quantity": target.get("available_quantity"),
        "price": target.get("price"),
        "title": target.get("title"),
        "permalink": target.get("permalink"),
    })

with open("/tmp/rocio_to_edilberto_results.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("CLONE_RESULTS=" + json.dumps(results, ensure_ascii=False))
