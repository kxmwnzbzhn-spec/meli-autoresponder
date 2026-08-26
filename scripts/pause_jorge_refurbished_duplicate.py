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
    response = requests.put(
        f"{API}/items/{DUPLICATE_ID}", headers=HJ,
        json={"available_quantity": 1}, timeout=TIMEOUT
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"No se pudo activar la oferta: {response.status_code} {response.text[:500]}"
        )
    active_ids = [DUPLICATE_ID]

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
