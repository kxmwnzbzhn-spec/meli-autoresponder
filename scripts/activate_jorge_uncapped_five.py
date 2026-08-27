#!/usr/bin/env python3
import json
import os
import time
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TIMEOUT = 30
ITEMS = [
    "MLM3402363017",
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
    timeout=TIMEOUT,
)
response.raise_for_status()
token_data = response.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(token_data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {token_data['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}

results = []
for item_id in ITEMS:
    before_response = requests.get(
        f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT
    )
    before_response.raise_for_status()
    before = before_response.json()
    if int(before.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(
            f"{item_id}: seller={before.get('seller_id')} esperado={SELLER_ID}"
        )

    update = requests.put(
        f"{API}/items/{item_id}",
        headers=HJ,
        json={"available_quantity": 1, "status": "active"},
        timeout=TIMEOUT,
    )
    if update.status_code not in (200, 201):
        results.append({
            "item_id": item_id,
            "status": "failed",
            "before_status": before.get("status"),
            "http": update.status_code,
            "error": update.text[:800],
        })
        continue

    final_response = requests.get(
        f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT
    )
    final_response.raise_for_status()
    final = final_response.json()
    verified = (
        final.get("status") == "active"
        and int(final.get("available_quantity") or 0) == 1
    )
    results.append({
        "item_id": item_id,
        "status": "verified" if verified else "failed_verification",
        "listing_status": final.get("status"),
        "quantity": final.get("available_quantity"),
        "title": final.get("title"),
        "permalink": final.get("permalink"),
    })

time.sleep(45)
for row in results:
    final_response = requests.get(
        f"{API}/items/{row['item_id']}", headers=H, timeout=TIMEOUT
    )
    final_response.raise_for_status()
    final = final_response.json()
    row["listing_status"] = final.get("status")
    row["quantity"] = final.get("available_quantity")
    row["status"] = (
        "verified"
        if final.get("status") == "active"
        and int(final.get("available_quantity") or 0) == 1
        else "failed_delayed_verification"
    )
    row["delayed_verification_seconds"] = 45

with open("/tmp/jorge_activate_uncapped_five.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("JORGE_UNCAPPED_FIVE_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
if not all(row.get("status") == "verified" for row in results):
    raise RuntimeError("Una o más publicaciones no quedaron activas con una pieza")
