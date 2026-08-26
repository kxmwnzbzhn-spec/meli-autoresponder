#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
TARGET_SELLER = 3640697853
KEEP_ID = "MLM3401276511"
DUPLICATE_ID = "MLM3401303117"
TIMEOUT = 30

r = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"],
    },
    timeout=TIMEOUT,
)
r.raise_for_status()
data = r.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {data['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}

def get(item_id):
    response = requests.get(f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != TARGET_SELLER:
        raise RuntimeError(f"{item_id}: vendedor inesperado {item.get('seller_id')}")
    return item

keep = get(KEEP_ID)
duplicate = get(DUPLICATE_ID)
if keep.get("user_product_id") != duplicate.get("user_product_id"):
    raise RuntimeError("Los IDs no corresponden al mismo producto; corrección abortada")

items = {KEEP_ID: keep, DUPLICATE_ID: duplicate}
active_ids = [item_id for item_id, item in items.items() if item.get("status") == "active"]
if not active_ids:
    upid = duplicate.get("user_product_id")
    stock_response = requests.get(
        f"{API}/user-products/{upid}/stock", headers=H, timeout=TIMEOUT
    )
    stock_response.raise_for_status()
    stock = stock_response.json()
    locations = [
        row for row in (stock.get("locations") or [])
        if row.get("type") != "meli_facility"
    ]
    if not locations:
        raise RuntimeError(f"{upid}: no hay ubicación editable de inventario")
    kinds = {row.get("type") for row in locations}
    if len(kinds) != 1:
        raise RuntimeError(f"{upid}: inventario mixto no seguro {sorted(kinds)}")
    kind = next(iter(kinds))
    stock_headers = dict(HJ)
    if stock_response.headers.get("x-version"):
        stock_headers["x-version"] = stock_response.headers["x-version"]
    if kind == "selling_address":
        stock_body = {"quantity": 1}
    elif kind == "seller_warehouse":
        stock_body = {"locations": []}
        first = True
        for row in locations:
            target = {"quantity": 1 if first else 0}
            first = False
            if row.get("store_id") is not None:
                target["store_id"] = row.get("store_id")
            if row.get("network_node_id") is not None:
                target["network_node_id"] = row.get("network_node_id")
            stock_body["locations"].append(target)
    else:
        raise RuntimeError(f"{upid}: tipo de inventario no soportado {kind}")
    response = requests.put(
        f"{API}/user-products/{upid}/stock/type/{kind}",
        headers=stock_headers, json=stock_body, timeout=TIMEOUT
    )
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"{upid}: stock 1 falló {response.status_code} {response.text[:500]}"
        )
    items = {KEEP_ID: get(KEEP_ID), DUPLICATE_ID: get(DUPLICATE_ID)}
    active_ids = [
        item_id for item_id, item in items.items() if item.get("status") == "active"
    ]

kept_id = active_ids[0]
for item_id in active_ids[1:]:
    response = requests.put(
        f"{API}/items/{item_id}", headers=HJ,
        json={"status": "paused"}, timeout=TIMEOUT
    )
    response.raise_for_status()

after = {item_id: get(item_id) for item_id in (KEEP_ID, DUPLICATE_ID)}
active_after = [
    item_id for item_id, item in after.items() if item.get("status") == "active"
]
if len(active_after) != 1:
    raise RuntimeError(f"Se esperaba una sola oferta activa; activas={active_after}")

kept_id = active_after[0]
paused_id = DUPLICATE_ID if kept_id == KEEP_ID else KEEP_ID

print("PAUSE_DUPLICATE_RESULT=" + json.dumps({
    "kept": KEEP_ID,
    "kept_status": keep_after.get("status"),
    "paused_duplicate": DUPLICATE_ID,
    "duplicate_status": duplicate_after.get("status"),
    "user_product_id": keep_after.get("user_product_id"),
}, ensure_ascii=False), flush=True)
