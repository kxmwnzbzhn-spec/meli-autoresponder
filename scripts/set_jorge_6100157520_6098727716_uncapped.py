#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TIMEOUT = 30
TARGET_PRICE = 499
ITEMS = ["MLM6100157520", "MLM6098727716"]
PRICE_ITEM = "MLM6100157520"

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
data = token.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
headers = {"Authorization": f"Bearer {data['access_token']}"}
json_headers = {**headers, "Content-Type": "application/json"}

results = []
for item_id in ITEMS:
    before_response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    before_response.raise_for_status()
    before = before_response.json()
    if int(before.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {before.get('seller_id')}")

    update_body = {"available_quantity": 1, "status": "active"}
    if item_id == PRICE_ITEM:
        update_body["price"] = TARGET_PRICE
    update = requests.put(
        f"{API}/items/{item_id}",
        headers=json_headers,
        json=update_body,
        timeout=TIMEOUT,
    )
    if update.status_code not in (200, 201):
        raise RuntimeError(f"{item_id}: actualización {update.status_code} {update.text[:800]}")

    final_response = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    final_response.raise_for_status()
    final = final_response.json()
    ok = final.get("status") == "active" and int(final.get("available_quantity") or 0) == 1
    if item_id == PRICE_ITEM:
        ok = ok and float(final.get("price") or 0) == float(TARGET_PRICE)
    results.append({
        "item_id": item_id,
        "title": final.get("title"),
        "status": final.get("status"),
        "available_quantity": final.get("available_quantity"),
        "price": final.get("price"),
        "verified": ok,
        "permalink": final.get("permalink"),
    })
    if not ok:
        raise RuntimeError(f"{item_id}: verificación falló: {results[-1]}")

print("JORGE_UNCAPPED_PRICE_RESULT=" + json.dumps(results, ensure_ascii=False), flush=True)
