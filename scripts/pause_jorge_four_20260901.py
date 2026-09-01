#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TIMEOUT = 30
ITEMS = [
    "MLM6097051428",
    "MLM6130979818",
    "MLM6097042780",
    "MLM3431032997",
]

access_token = os.environ.get("MELI_ACCESS_TOKEN", "").strip()
if not access_token:
    token = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["MELI_APP_ID_NEW"],
            "client_secret": os.environ["MELI_APP_SECRET_NEW"],
            "refresh_token": os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"],
        },
        timeout=TIMEOUT,
    )
    token.raise_for_status()
    token_data = token.json()
    access_token = token_data["access_token"]
    with open("/tmp/jorge_luis_rotated_token", "w") as handle:
        handle.write(token_data.get("refresh_token", ""))
    with open("/tmp/jorge_luis_access_token", "w") as handle:
        handle.write(access_token)

headers = {"Authorization": f"Bearer {access_token}"}
json_headers = {**headers, "Content-Type": "application/json"}
results = []

for item_id in ITEMS:
    before_response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    before_response.raise_for_status()
    before = before_response.json()
    if int(before.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {before.get('seller_id')}")

    if before.get("status") == "active":
        update = requests.put(
            f"{API}/items/{item_id}",
            headers=json_headers,
            json={"status": "paused"},
            timeout=TIMEOUT,
        )
        if update.status_code not in (200, 201):
            raise RuntimeError(f"{item_id}: pause {update.status_code} {update.text[:800]}")

    final_response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    final_response.raise_for_status()
    final = final_response.json()
    verified = final.get("status") != "active"
    row = {
        "item_id": item_id,
        "title": final.get("title"),
        "status_before": before.get("status"),
        "status": final.get("status"),
        "available_quantity": final.get("available_quantity"),
        "verified_not_active": verified,
        "permalink": final.get("permalink"),
    }
    results.append(row)
    if not verified:
        raise RuntimeError(f"{item_id}: sigue activa: {row}")

print("JORGE_PAUSE_FOUR_RESULT=" + json.dumps(results, ensure_ascii=False), flush=True)
