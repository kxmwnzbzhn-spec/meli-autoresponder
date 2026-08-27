#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
ITEM_ID = "MLM3409049385"
TARGET_PRICE = 699
TIMEOUT = 30

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
data = response.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {data['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}

before_response = requests.get(f"{API}/items/{ITEM_ID}", headers=H, timeout=TIMEOUT)
before_response.raise_for_status()
before = before_response.json()
if int(before.get("seller_id") or 0) != SELLER_ID:
    raise RuntimeError(
        f"{ITEM_ID}: seller={before.get('seller_id')} esperado={SELLER_ID}"
    )

update = requests.put(
    f"{API}/items/{ITEM_ID}",
    headers=HJ,
    json={"price": TARGET_PRICE},
    timeout=TIMEOUT,
)
if update.status_code not in (200, 201):
    raise RuntimeError(
        f"{ITEM_ID}: precio HTTP={update.status_code} BODY={update.text[:1200]}"
    )

final_response = requests.get(f"{API}/items/{ITEM_ID}", headers=H, timeout=TIMEOUT)
final_response.raise_for_status()
final = final_response.json()
if float(final.get("price") or 0) != float(TARGET_PRICE):
    raise RuntimeError(
        f"{ITEM_ID}: precio no confirmado; actual={final.get('price')}"
    )

result = {
    "item_id": ITEM_ID,
    "status": "verified",
    "old_price": before.get("price"),
    "new_price": final.get("price"),
    "listing_status": final.get("status"),
    "title": final.get("title"),
    "permalink": final.get("permalink"),
}
print("JORGE_PRICE_699_RESULT=" + json.dumps(result, ensure_ascii=False), flush=True)
