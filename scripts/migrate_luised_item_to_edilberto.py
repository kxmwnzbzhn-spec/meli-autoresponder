#!/usr/bin/env python3
"""Migración controlada de MLM3356000563: LuisEd -> Edilberto.

Fase clone: crea o reutiliza una publicación equivalente en Edilberto y la deja activa con qty=1.
Fase finalize: verifica el destino y solo entonces cierra y marca eliminada la fuente.
"""
import json
import os
import sys
import requests

API = "https://api.mercadolibre.com"
SOURCE_ID = "MLM3356000563"
SOURCE_SELLER = 3584846108
TARGET_SELLER = 3616975257
MODE = os.environ.get("MIGRATION_MODE", "clone").strip().lower()
TARGET_ITEM_ID = os.environ.get("TARGET_ITEM_ID", "").strip().upper()
TIMEOUT = 25

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


SOURCE_TOKEN = refresh("MELI_REFRESH_TOKEN_LUISED", "/tmp/luised_rotated_token")
TARGET_TOKEN = refresh("MELI_REFRESH_TOKEN_EDILBERTO", "/tmp/edilberto_rotated_token")
HS = {"Authorization": f"Bearer {SOURCE_TOKEN}"}
HT = {"Authorization": f"Bearer {TARGET_TOKEN}"}
HST = {**HS, "Content-Type": "application/json"}
HTJ = {**HT, "Content-Type": "application/json"}


def require_item(item_id, headers, seller_id):
    response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != seller_id:
        raise RuntimeError(
            f"{item_id}: seller inesperado {item.get('seller_id')}; esperado {seller_id}"
        )
    return item


def target_candidates(catalog_product_id):
    response = requests.get(
        f"{API}/users/{TARGET_SELLER}/items/search",
        headers=HT,
        params={"status": "active", "limit": 100},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    found = []
    for item_id in response.json().get("results") or []:
        try:
            result = require_item(item_id, HT, TARGET_SELLER)
        except Exception:
            continue
        if (
            result.get("catalog_product_id") == catalog_product_id
            and result.get("condition") == "new"
        ):
            found.append(item_id)
    return [item_id for item_id in found if item_id]


def safe_attributes(source):
    skip = {
        "SELLER_SKU", "HAZMAT_TRANSPORTABILITY", "ITEM_CONDITION",
        "PACKAGE_LENGTH", "PACKAGE_WEIGHT", "PACKAGE_WIDTH", "PACKAGE_HEIGHT",
        "SHIPMENT_PACKING", "PRODUCT_FEATURES",
    }
    output = []
    for attribute in source.get("attributes") or []:
        attribute_id = attribute.get("id")
        if not attribute_id or attribute_id in skip:
            continue
        value_id = attribute.get("value_id")
        value_name = attribute.get("value_name")
        if value_id:
            output.append({"id": attribute_id, "value_id": value_id})
        elif value_name:
            output.append({"id": attribute_id, "value_name": value_name})
    return output


def create_target(source):
    catalog_product_id = source.get("catalog_product_id")
    for candidate in target_candidates(catalog_product_id):
        existing = require_item(candidate, HT, TARGET_SELLER)
        if existing.get("status") != "closed" and not existing.get("deleted"):
            update = requests.put(
                f"{API}/items/{candidate}",
                headers=HTJ,
                json={"available_quantity": 1, "status": "active"},
                timeout=TIMEOUT,
            )
            if update.status_code not in (200, 201):
                raise RuntimeError(
                    f"{candidate}: no se pudo normalizar destino: "
                    f"{update.status_code} {update.text[:400]}"
                )
            print(f"REUSED_TARGET={candidate}")
            return candidate

    family_name = source.get("family_name") or source.get("title") or "Sony SRS-XB100"
    attributes = [{"id": "ITEM_CONDITION", "value_name": "Nuevo"}]
    for attribute in source.get("attributes") or []:
        if attribute.get("id") in {"GTIN", "EAN", "UPC"}:
            value = str(attribute.get("value_name") or "").strip()
            if value.isdigit() and 8 <= len(value) <= 14:
                attributes.insert(0, {"id": "GTIN", "value_name": value})
                break
    payload = {
        "site_id": "MLM",
        "family_name": family_name[:60],
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
            "free_shipping": bool((source.get("shipping") or {}).get("free_shipping")),
        },
    }
    created = requests.post(
        f"{API}/items", headers=HTJ, json=payload, timeout=40
    )
    if created.status_code not in (200, 201):
        raise RuntimeError(f"clone POST {created.status_code}: {created.text[:1200]}")

    target_id = created.json().get("id")
    if not target_id:
        raise RuntimeError(f"clone sin id: {created.text[:800]}")

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
    print(f"CREATED_TARGET={target_id}")
    return target_id


def register_priority(target_id, title):
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not sb_url or not sb_key:
        print("PRIORITY_SKIPPED=no_supabase")
        return
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    response = requests.post(
        f"{sb_url}/rest/v1/meli_priority_replenish",
        headers=headers,
        json={
            "item_id": target_id,
            "account": "EDILBERTO",
            "default_qty": 1,
            "product_name": title[:200],
        },
        timeout=TIMEOUT,
    )
    if response.status_code not in (200, 201, 204):
        print(
            f"PRIORITY_WARNING={response.status_code}: {response.text[:500]}"
        )
        return
    print("PRIORITY_REGISTERED=true")


def verify_target(target_id):
    item = require_item(target_id, HT, TARGET_SELLER)
    if item.get("status") != "active" or int(item.get("available_quantity") or 0) != 1:
        response = requests.put(
            f"{API}/items/{target_id}",
            headers=HTJ,
            json={"available_quantity": 1, "status": "active"},
            timeout=TIMEOUT,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"{target_id}: normalización final {response.status_code} "
                f"{response.text[:500]}"
            )
        item = require_item(target_id, HT, TARGET_SELLER)
    if item.get("status") != "active" or int(item.get("available_quantity") or 0) != 1:
        raise RuntimeError(
            f"{target_id}: verificación falló status={item.get('status')} "
            f"qty={item.get('available_quantity')}"
        )
    if item.get("condition") != "new":
        raise RuntimeError(
            f"{target_id}: condition={item.get('condition')} esperado=new"
        )
    print(
        f"TARGET_VERIFIED={target_id} status={item.get('status')} "
        f"qty={item.get('available_quantity')} price={item.get('price')} "
        f"title={item.get('title')}"
    )
    return item


def delete_source():
    source = require_item(SOURCE_ID, HS, SOURCE_SELLER)
    if source.get("status") != "closed":
        closed = requests.put(
            f"{API}/items/{SOURCE_ID}",
            headers=HST,
            json={"status": "closed"},
            timeout=TIMEOUT,
        )
        if closed.status_code not in (200, 201):
            raise RuntimeError(
                f"source close {closed.status_code}: {closed.text[:600]}"
            )
    deleted = requests.put(
        f"{API}/items/{SOURCE_ID}",
        headers=HST,
        json={"deleted": "true"},
        timeout=TIMEOUT,
    )
    if deleted.status_code not in (200, 201):
        raise RuntimeError(
            f"source delete {deleted.status_code}: {deleted.text[:600]}"
        )
    final_source = require_item(SOURCE_ID, HS, SOURCE_SELLER)
    if final_source.get("status") != "closed" or not final_source.get("deleted"):
        raise RuntimeError(
            f"source no quedó eliminada: status={final_source.get('status')} "
            f"deleted={final_source.get('deleted')}"
        )
    print(
        f"SOURCE_DELETED={SOURCE_ID} status={final_source.get('status')} "
        f"deleted={final_source.get('deleted')}"
    )


source = require_item(SOURCE_ID, HS, SOURCE_SELLER)
print(
    f"SOURCE={SOURCE_ID} status={source.get('status')} price={source.get('price')} "
    f"catalog_product_id={source.get('catalog_product_id')} title={source.get('title')}"
)

if MODE == "clone":
    target_id = create_target(source)
    target = verify_target(target_id)
    register_priority(target_id, target.get("title") or source.get("title") or "")
    with open("/tmp/new_item_id", "w") as handle:
        handle.write(target_id)
    print(f"NEW_ITEM_ID={target_id}")
elif MODE == "finalize":
    if not TARGET_ITEM_ID:
        raise RuntimeError("TARGET_ITEM_ID requerido para finalizar")
    verify_target(TARGET_ITEM_ID)
    delete_source()
    print(f"MIGRATION_COMPLETE={SOURCE_ID}->{TARGET_ITEM_ID}")
else:
    raise RuntimeError(f"MIGRATION_MODE inválido: {MODE}")
