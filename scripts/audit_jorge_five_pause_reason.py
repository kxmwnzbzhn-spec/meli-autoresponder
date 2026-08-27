#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TIMEOUT = 30
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
    timeout=TIMEOUT,
)
response.raise_for_status()
data = response.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {data['access_token']}"}

seller_items = []
offset = 0
while offset < 2000:
    search = requests.get(
        f"{API}/users/{SELLER_ID}/items/search",
        headers=H,
        params={"limit": 100, "offset": offset},
        timeout=TIMEOUT,
    )
    search.raise_for_status()
    ids = search.json().get("results") or []
    seller_items.extend(ids)
    if len(ids) < 100:
        break
    offset += 100

details = {}
for item_id in seller_items:
    value = requests.get(f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT)
    if value.status_code == 200:
        details[item_id] = value.json()

rows = []
for item_id in ITEMS:
    item = details.get(item_id)
    if not item:
        response = requests.get(f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT)
        response.raise_for_status()
        item = response.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    upid = item.get("user_product_id")
    shared = [
        {
            "item_id": other_id,
            "status": other.get("status"),
            "sub_status": other.get("sub_status"),
            "quantity": other.get("available_quantity"),
            "title": other.get("title"),
        }
        for other_id, other in details.items()
        if other_id != item_id and upid and other.get("user_product_id") == upid
    ]
    stock = None
    if upid:
        stock_response = requests.get(
            f"{API}/user-products/{upid}/stock", headers=H, timeout=TIMEOUT
        )
        if stock_response.status_code == 200:
            stock = stock_response.json()
    rows.append({
        "item_id": item_id,
        "title": item.get("title"),
        "status": item.get("status"),
        "sub_status": item.get("sub_status"),
        "available_quantity": item.get("available_quantity"),
        "inventory_id": item.get("inventory_id"),
        "user_product_id": upid,
        "catalog_product_id": item.get("catalog_product_id"),
        "shipping": item.get("shipping"),
        "stock": stock,
        "shared_user_product_listings": shared,
    })

print("JORGE_PAUSE_AUDIT=" + json.dumps(rows, ensure_ascii=False), flush=True)
