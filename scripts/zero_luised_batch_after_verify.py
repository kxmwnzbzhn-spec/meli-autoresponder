#!/usr/bin/env python3
"""Pone en cero cuatro fuentes de LuisEd solo tras verificar destinos Edilberto."""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SOURCE_SELLER = 3584846108
TARGET_SELLER = 3616975257
SOURCE_IDS = ["MLM3356015807", "MLM3356017195", "MLM3355976643", "MLM3356015233"]
TARGET_IDS = ["MLM6061793358", "MLM6061831150", "MLM6061856108", "MLM6061793370"]
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
HSJ = {**HS, "Content-Type": "application/json"}


def get_item(item_id, headers, seller_id):
    response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != seller_id:
        raise RuntimeError(
            f"{item_id}: seller={item.get('seller_id')} esperado={seller_id}"
        )
    return item


def verify_targets():
    results = []
    for target_id in TARGET_IDS:
        item = get_item(target_id, HT, TARGET_SELLER)
        if item.get("status") != "active" or int(item.get("available_quantity") or 0) != 1:
            raise RuntimeError(
                f"{target_id}: destino no seguro status={item.get('status')} "
                f"qty={item.get('available_quantity')}"
            )
        results.append({
            "id": target_id,
            "status": item.get("status"),
            "quantity": item.get("available_quantity"),
            "title": item.get("title"),
        })
        print(f"TARGET_OK {target_id} active qty=1", flush=True)
    return results


def zero_user_product(item):
    upid = item.get("user_product_id")
    if not upid:
        return False
    response = requests.get(
        f"{API}/user-products/{upid}/stock", headers=HS, timeout=TIMEOUT
    )
    if response.status_code != 200:
        return False
    stock = response.json()
    locations = [
        row for row in (stock.get("locations") or [])
        if row.get("type") != "meli_facility"
    ]
    if not locations:
        return False
    kinds = {row.get("type") for row in locations}
    if len(kinds) != 1:
        raise RuntimeError(f"{upid}: tipos de stock mixtos {sorted(kinds)}")
    kind = next(iter(kinds))
    headers = dict(HSJ)
    if response.headers.get("x-version"):
        headers["x-version"] = response.headers["x-version"]
    if kind == "selling_address":
        body = {"quantity": 0}
    elif kind == "seller_warehouse":
        out = []
        for row in locations:
            target = {"quantity": 0}
            if row.get("store_id") is not None:
                target["store_id"] = row.get("store_id")
            if row.get("network_node_id") is not None:
                target["network_node_id"] = row.get("network_node_id")
            out.append(target)
        body = {"locations": out}
    else:
        raise RuntimeError(f"{upid}: tipo no soportado {kind}")
    updated = requests.put(
        f"{API}/user-products/{upid}/stock/type/{kind}",
        headers=headers,
        json=body,
        timeout=TIMEOUT,
    )
    if updated.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"{upid}: stock zero {updated.status_code} {updated.text[:500]}"
        )
    print(f"USER_PRODUCT_ZERO {upid} type={kind}", flush=True)
    return True


def zero_source(source_id):
    item = get_item(source_id, HS, SOURCE_SELLER)
    response = requests.put(
        f"{API}/items/{source_id}",
        headers=HSJ,
        json={"available_quantity": 0},
        timeout=TIMEOUT,
    )
    if response.status_code not in (200, 201):
        if not zero_user_product(item):
            raise RuntimeError(
                f"{source_id}: qty zero {response.status_code} {response.text[:600]}"
            )
    final = get_item(source_id, HS, SOURCE_SELLER)
    if int(final.get("available_quantity") or 0) != 0:
        if not zero_user_product(final):
            raise RuntimeError(
                f"{source_id}: qty final={final.get('available_quantity')}"
            )
        final = get_item(source_id, HS, SOURCE_SELLER)
    if int(final.get("available_quantity") or 0) != 0:
        raise RuntimeError(
            f"{source_id}: no quedó en cero qty={final.get('available_quantity')}"
        )
    print(
        f"SOURCE_ZERO {source_id} status={final.get('status')} qty=0 "
        f"title={final.get('title')}",
        flush=True,
    )
    return {
        "id": source_id,
        "status": final.get("status"),
        "quantity": final.get("available_quantity"),
        "title": final.get("title"),
    }


targets = verify_targets()
sources = [zero_source(source_id) for source_id in SOURCE_IDS]
result = {"targets": targets, "sources": sources}
with open("/tmp/zero_sources_results.json", "w") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
print("ZERO_RESULTS=" + json.dumps(result, ensure_ascii=False), flush=True)
