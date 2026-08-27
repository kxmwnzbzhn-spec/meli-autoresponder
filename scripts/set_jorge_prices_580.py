#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TARGET_PRICE = 580
TIMEOUT = 30
ITEMS = [
    "MLM6097042780",
    "MLM6097051428",
    "MLM6097038456",
    "MLM6097051040",
    "MLM6097030480",
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
        json={"price": TARGET_PRICE},
        timeout=TIMEOUT,
    )
    if update.status_code not in (200, 201):
        results.append({
            "item_id": item_id,
            "status": "failed",
            "old_price": before.get("price"),
            "http": update.status_code,
            "error": update.text[:800],
        })
        continue

    final_response = requests.get(
        f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT
    )
    final_response.raise_for_status()
    final = final_response.json()
    verified = float(final.get("price") or 0) == float(TARGET_PRICE)
    results.append({
        "item_id": item_id,
        "status": "verified" if verified else "failed_verification",
        "old_price": before.get("price"),
        "new_price": final.get("price"),
        "listing_status": final.get("status"),
        "title": final.get("title"),
        "permalink": final.get("permalink"),
    })

with open("/tmp/jorge_price_580_results.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("JORGE_PRICE_580_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
if not all(row.get("status") == "verified" for row in results):
    raise RuntimeError("Una o más publicaciones no confirmaron el precio 580")
