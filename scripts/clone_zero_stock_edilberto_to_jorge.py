#!/usr/bin/env python3
"""Clone exhausted Edilberto catalog listings to Jorge without exposing stock."""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_SELLER = 3616975257
TARGET_SELLER = 3640697853
DEFAULT_SOURCE_IDS = [
    "MLM6075595766",
    "MLM3387189275",
    "MLM6075580366",
    "MLM6075497680",
    "MLM6075502880",
    "MLM6075597440",
]
raw_source = os.environ.get("SOURCE_ITEM_ID", "").strip().upper().replace("-", "")
SOURCE_IDS = (
    [raw_source if raw_source.startswith("MLM") else f"MLM{raw_source}"]
    if raw_source
    else DEFAULT_SOURCE_IDS
)
TIMEOUT = 30
CID = os.environ["MELI_APP_ID_NEW"]
CSECRET = os.environ["MELI_APP_SECRET_NEW"]


def refresh(secret, path):
    response = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CID,
            "client_secret": CSECRET,
            "refresh_token": os.environ[secret],
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    with open(path, "w") as handle:
        handle.write(data.get("refresh_token", ""))
    return {"Authorization": f"Bearer {data['access_token']}"}


HS = refresh("MELI_REFRESH_TOKEN_EDILBERTO", "/tmp/edilberto_rotated_token")
HT = refresh("MELI_REFRESH_TOKEN_JORGE_LUIS", "/tmp/jorge_luis_rotated_token")
HTJ = {**HT, "Content-Type": "application/json"}


def item(item_id, headers, seller):
    response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    value = response.json()
    if int(value.get("seller_id") or 0) != seller:
        raise RuntimeError(f"{item_id}: seller inesperado {value.get('seller_id')}")
    return value


def target_catalogs():
    values = {}
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
        for target_id in ids:
            try:
                target = item(target_id, HT, TARGET_SELLER)
            except Exception:
                continue
            catalog = target.get("catalog_product_id")
            if catalog and target.get("catalog_listing") and not target.get("deleted"):
                values.setdefault(catalog, target)
        if len(ids) < 100:
            break
        offset += 100
    return values


def gtin(source):
    for attribute in source.get("attributes") or []:
        if attribute.get("id") in {"GTIN", "EAN", "UPC"}:
            value = str(attribute.get("value_name") or "").strip()
            if value.isdigit() and 8 <= len(value) <= 14:
                return value
    return None


catalogs = target_catalogs()
results = []
for source_id in SOURCE_IDS:
    source = item(source_id, HS, SOURCE_SELLER)
    catalog = source.get("catalog_product_id")
    if not catalog or not source.get("catalog_listing"):
        raise RuntimeError(f"{source_id}: no es publicación de catálogo")
    if int(source.get("available_quantity") or 0) != 0:
        raise RuntimeError(
            f"{source_id}: ya tiene existencia {source.get('available_quantity')}; "
            "se abortó el lote para no registrar inventario incorrecto"
        )

    existing = catalogs.get(catalog)
    if existing:
        target_id = existing.get("id")
        if existing.get("condition") != "new":
            raise RuntimeError(
                f"{source_id}: {target_id} ya existe con condición "
                f"{existing.get('condition')}; no se duplicó"
            )
        if existing.get("status") not in {"active", "paused"}:
            results.append({
                "source_id": source_id,
                "target_id": target_id,
                "action": "existing_unmodified",
                "status": existing.get("status"),
                "quantity": existing.get("available_quantity"),
                "catalog_product_id": catalog,
                "title": existing.get("title"),
                "price": existing.get("price"),
                "permalink": existing.get("permalink"),
            })
            continue
        update = requests.put(
            f"{API}/items/{target_id}",
            headers=HTJ,
            json={"price": source.get("price"), "status": "paused"},
            timeout=TIMEOUT,
        )
        if update.status_code not in (200, 201):
            raise RuntimeError(
                f"{target_id}: no se pudo pausar {update.status_code} {update.text[:500]}"
            )
        action = "reused_paused"
    else:
        attributes = [{"id": "ITEM_CONDITION", "value_name": "Nuevo"}]
        code = gtin(source)
        if code:
            attributes.insert(0, {"id": "GTIN", "value_name": code})
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
            "catalog_product_id": catalog,
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
        created = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=45)
        if created.status_code not in (200, 201):
            raise RuntimeError(
                f"{source_id}: publicación falló {created.status_code} "
                f"{created.text[:1000]}"
            )
        target_id = created.json().get("id")
        created_item = item(target_id, HT, TARGET_SELLER)
        if created_item.get("status") == "active":
            paused = requests.put(
                f"{API}/items/{target_id}",
                headers=HTJ,
                json={"status": "paused"},
                timeout=TIMEOUT,
            )
            if paused.status_code not in (200, 201):
                raise RuntimeError(
                    f"{target_id}: creado pero no pausado {paused.status_code} "
                    f"{paused.text[:700]}"
                )
            action = "created_paused"
        elif created_item.get("status") == "under_review":
            action = "created_under_review"
        elif created_item.get("status") == "paused":
            action = "created_paused"
        else:
            raise RuntimeError(
                f"{target_id}: estado inesperado tras crear "
                f"{created_item.get('status')}"
            )
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
    target = item(target_id, HT, TARGET_SELLER)
    checks = {
        "not_sellable": target.get("status") in {"paused", "under_review"},
        "new": target.get("condition") == "new",
        "catalog": bool(target.get("catalog_listing")),
        "same_catalog": target.get("catalog_product_id") == catalog,
    }
    if not all(checks.values()):
        raise RuntimeError(f"{target_id}: verificación falló {checks}")
    catalogs[catalog] = target
    results.append({
        "source_id": source_id,
        "target_id": target_id,
        "action": action,
        "title": target.get("title"),
        "price": target.get("price"),
        "condition": target.get("condition"),
        "status": target.get("status"),
        "quantity": target.get("available_quantity"),
        "real_stock": 0,
        "catalog_product_id": catalog,
        "permalink": target.get("permalink"),
    })

with open("/tmp/jorge_zero_stock_batch.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("ZERO_STOCK_CLONE_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
