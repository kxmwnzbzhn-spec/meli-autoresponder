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

if keep.get("status") != "active":
    response = requests.put(
        f"{API}/items/{KEEP_ID}", headers=HJ,
        json={"status": "active", "available_quantity": 1}, timeout=TIMEOUT
    )
    response.raise_for_status()

if duplicate.get("status") == "active":
    response = requests.put(
        f"{API}/items/{DUPLICATE_ID}", headers=HJ,
        json={"status": "paused"}, timeout=TIMEOUT
    )
    response.raise_for_status()

keep_after = get(KEEP_ID)
duplicate_after = get(DUPLICATE_ID)
if keep_after.get("status") != "active" or duplicate_after.get("status") == "active":
    raise RuntimeError("No se confirmó la corrección reversible")

print("PAUSE_DUPLICATE_RESULT=" + json.dumps({
    "kept": KEEP_ID,
    "kept_status": keep_after.get("status"),
    "paused_duplicate": DUPLICATE_ID,
    "duplicate_status": duplicate_after.get("status"),
    "user_product_id": keep_after.get("user_product_id"),
}, ensure_ascii=False), flush=True)
