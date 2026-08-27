#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
ITEMS = [
    "MLM6100171026",
    "MLM6100158830",
    "MLM3403250729",
    "MLM3403240547",
    "MLM3403241131",
]
response = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"],
    },
    timeout=30,
)
response.raise_for_status()
data = response.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {data['access_token']}"}

rows = []
for item_id in ITEMS:
    result = requests.get(f"{API}/items/{item_id}", headers=H, timeout=30)
    result.raise_for_status()
    item = result.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado")
    rows.append({
        "item_id": item_id,
        "status": item.get("status"),
        "sub_status": item.get("sub_status"),
        "available_quantity": item.get("available_quantity"),
    })
print("JORGE_PAUSE_STATUS=" + json.dumps(rows), flush=True)
