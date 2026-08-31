#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
ITEM_ID = "MLM6099889822"
TIMEOUT = 30

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

before_response = requests.get(f"{API}/items/{ITEM_ID}", headers=headers, timeout=TIMEOUT)
before_response.raise_for_status()
before = before_response.json()
if int(before.get("seller_id") or 0) != SELLER_ID:
    raise RuntimeError(f"{ITEM_ID}: seller inesperado {before.get('seller_id')}")

update = requests.put(
    f"{API}/items/{ITEM_ID}",
    headers=json_headers,
    json={"available_quantity": 1, "status": "active"},
    timeout=TIMEOUT,
)
if update.status_code not in (200, 201):
    raise RuntimeError(f"{ITEM_ID}: actualización {update.status_code} {update.text[:800]}")

final_response = requests.get(f"{API}/items/{ITEM_ID}", headers=headers, timeout=TIMEOUT)
final_response.raise_for_status()
final = final_response.json()
verified = final.get("status") == "active" and int(final.get("available_quantity") or 0) == 1
result = {
    "item_id": ITEM_ID,
    "title": final.get("title"),
    "status": final.get("status"),
    "available_quantity": final.get("available_quantity"),
    "price": final.get("price"),
    "verified": verified,
    "permalink": final.get("permalink"),
}
print("JORGE_6099889822_UNCAPPED_RESULT=" + json.dumps(result, ensure_ascii=False), flush=True)
if not verified:
    raise RuntimeError(f"{ITEM_ID}: verificación falló: {result}")
