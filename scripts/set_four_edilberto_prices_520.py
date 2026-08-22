#!/usr/bin/env python3
"""Fija en $520 las cuatro publicaciones autorizadas de Edilberto."""
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
TARGET_IDS = ["MLM6061793358", "MLM6061831150", "MLM6061856108", "MLM6061793370"]
PRICE = 520
TIMEOUT = 30

response = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    },
    timeout=TIMEOUT,
)
response.raise_for_status()
token_data = response.json()
with open("/tmp/edilberto_rotated_token", "w") as handle:
    handle.write(token_data.get("refresh_token", ""))
headers = {"Authorization": f"Bearer {token_data['access_token']}"}
json_headers = {**headers, "Content-Type": "application/json"}

results = []
for item_id in TARGET_IDS:
    current_response = requests.get(
        f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT
    )
    current_response.raise_for_status()
    current = current_response.json()
    if int(current.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(
            f"{item_id}: seller={current.get('seller_id')} esperado={SELLER_ID}"
        )
    if current.get("status") not in {"active", "paused", "under_review"}:
        raise RuntimeError(f"{item_id}: status no modificable {current.get('status')}")
    old_price = current.get("price")
    updated = requests.put(
        f"{API}/items/{item_id}",
        headers=json_headers,
        json={"price": PRICE},
        timeout=TIMEOUT,
    )
    if updated.status_code not in (200, 201):
        raise RuntimeError(
            f"{item_id}: price PUT {updated.status_code} {updated.text[:600]}"
        )
    final_response = requests.get(
        f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT
    )
    final_response.raise_for_status()
    final = final_response.json()
    if float(final.get("price") or 0) != float(PRICE):
        raise RuntimeError(
            f"{item_id}: price final={final.get('price')} esperado={PRICE}"
        )
    result = {
        "id": item_id,
        "old_price": old_price,
        "new_price": final.get("price"),
        "status": final.get("status"),
        "quantity": final.get("available_quantity"),
        "title": final.get("title"),
        "permalink": final.get("permalink"),
    }
    results.append(result)
    print(
        f"PRICE_OK {item_id} {old_price}->{final.get('price')} "
        f"status={final.get('status')} qty={final.get('available_quantity')}",
        flush=True,
    )

with open("/tmp/set_four_prices_results.json", "w") as handle:
    json.dump(results, handle, ensure_ascii=False, indent=2)
print("PRICE_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
