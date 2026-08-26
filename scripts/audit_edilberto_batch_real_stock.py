#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
ITEMS = [
    "MLM6075598700",
    "MLM6075595766",
    "MLM3387189275",
    "MLM6075580366",
    "MLM6075497680",
    "MLM6075502880",
    "MLM6075597440",
]
REGISTERED_INITIAL = {}
TIMEOUT = 30

r = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    },
    timeout=TIMEOUT,
)
r.raise_for_status()
data = r.json()
with open("/tmp/edilberto_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {data['access_token']}"}


def paid_units(item_id):
    total = 0
    offset = 0
    while True:
        response = requests.get(
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
        response.raise_for_status()
        body = response.json()
        rows = body.get("results") or []
        for order in rows:
            if order.get("status") in {"cancelled", "invalid"}:
                continue
            tags = set(order.get("tags") or [])
            approved = any(
                payment.get("status") == "approved"
                for payment in (order.get("payments") or [])
            )
            if (
                order.get("status") not in {"paid", "partially_refunded"}
                and "paid" not in tags
                and not approved
            ):
                continue
            for line in order.get("order_items") or []:
                if (line.get("item") or {}).get("id") == item_id:
                    total += int(line.get("quantity") or 0)
        offset += len(rows)
        if not rows or offset >= int((body.get("paging") or {}).get("total") or 0):
            break
    return total


rows = []
for item_id in ITEMS:
    response = requests.get(f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    units = paid_units(item_id)
    initial = REGISTERED_INITIAL.get(item_id)
    editable_stock = None
    stock_type = None
    upid = item.get("user_product_id")
    if upid:
        stock_response = requests.get(
            f"{API}/user-products/{upid}/stock", headers=H, timeout=TIMEOUT
        )
        if stock_response.status_code == 200:
            editable = [
                row for row in (stock_response.json().get("locations") or [])
                if row.get("type") != "meli_facility"
            ]
            editable_stock = sum(int(row.get("quantity") or 0) for row in editable)
            stock_type = sorted({row.get("type") for row in editable})
    remaining = max(0, initial - units) if initial is not None else None
    rows.append({
        "item_id": item_id,
        "title": item.get("title"),
        "status": item.get("status"),
        "sub_status": item.get("sub_status"),
        "condition": item.get("condition"),
        "catalog_product_id": item.get("catalog_product_id"),
        "catalog_listing": item.get("catalog_listing"),
        "price": item.get("price"),
        "initial_quantity_meli": item.get("initial_quantity"),
        "visible_available_quantity": item.get("available_quantity"),
        "sold_quantity_meli": item.get("sold_quantity"),
        "paid_units_verified": units,
        "registered_initial_real_stock": initial,
        "registered_remaining_real_stock": remaining,
        "editable_stock": editable_stock,
        "stock_type": stock_type,
        "user_product_id": upid,
    })
print("BATCH_STOCK_AUDIT=" + json.dumps(rows, ensure_ascii=False), flush=True)
