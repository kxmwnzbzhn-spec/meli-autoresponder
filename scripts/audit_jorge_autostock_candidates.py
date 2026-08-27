#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TIMEOUT = 30
ITEMS = [
    "MLM6099889822", "MLM6097042780", "MLM6100171026", "MLM3401279297",
    "MLM6100158830", "MLM3402386723", "MLM3402363017", "MLM3402390259",
    "MLM6098727716", "MLM6097051040", "MLM6097038456", "MLM6097051428",
    "MLM3403240547", "MLM3403241131", "MLM3401288599", "MLM6097030480",
    "MLM3401292527", "MLM3401303117", "MLM3403250729", "MLM6100157520",
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


def paid_units(item_id):
    total = 0
    offset = 0
    while True:
        result = requests.get(
            f"{API}/orders/search",
            headers=H,
            params={
                "seller": SELLER_ID,
                "q": item_id,
                "limit": 50,
                "offset": offset,
                "sort": "date_asc",
            },
            timeout=TIMEOUT,
        )
        result.raise_for_status()
        body = result.json()
        orders = body.get("results") or []
        for order in orders:
            if order.get("status") in {"cancelled", "invalid"}:
                continue
            approved = any(
                payment.get("status") == "approved"
                for payment in (order.get("payments") or [])
            )
            if (
                order.get("status") not in {"paid", "partially_refunded"}
                and "paid" not in set(order.get("tags") or [])
                and not approved
            ):
                continue
            for line in order.get("order_items") or []:
                if (line.get("item") or {}).get("id") == item_id:
                    total += int(line.get("quantity") or 0)
        offset += len(orders)
        if not orders or offset >= int((body.get("paging") or {}).get("total") or 0):
            return total


rows = []
for item_id in ITEMS:
    result = requests.get(f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT)
    result.raise_for_status()
    item = result.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    editable_stock = None
    stock_types = None
    upid = item.get("user_product_id")
    if upid:
        stock = requests.get(
            f"{API}/user-products/{upid}/stock", headers=H, timeout=TIMEOUT
        )
        if stock.status_code == 200:
            editable = [
                location for location in (stock.json().get("locations") or [])
                if location.get("type") != "meli_facility"
            ]
            editable_stock = sum(
                int(location.get("quantity") or 0) for location in editable
            )
            stock_types = sorted({location.get("type") for location in editable})
    rows.append({
        "item_id": item_id,
        "title": item.get("title"),
        "status": item.get("status"),
        "sub_status": item.get("sub_status"),
        "condition": item.get("condition"),
        "catalog_product_id": item.get("catalog_product_id"),
        "price": item.get("price"),
        "initial_quantity_meli": item.get("initial_quantity"),
        "available_quantity": item.get("available_quantity"),
        "sold_quantity_meli": item.get("sold_quantity"),
        "paid_units_verified": paid_units(item_id),
        "editable_stock": editable_stock,
        "stock_types": stock_types,
        "user_product_id": upid,
        "permalink": item.get("permalink"),
    })

with open("/tmp/jorge_autostock_candidates.json", "w") as handle:
    json.dump(rows, handle, ensure_ascii=False, indent=2)
print("JORGE_AUTOSTOCK_AUDIT=" + json.dumps(rows, ensure_ascii=False), flush=True)
