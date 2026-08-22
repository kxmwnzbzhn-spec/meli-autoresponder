#!/usr/bin/env python3
"""Resumen de ventas del día para Edilberto en horario de Ciudad de México."""
import json
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
TIMEOUT = 30
TZ = ZoneInfo("America/Mexico_City")

token_response = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    },
    timeout=TIMEOUT,
)
token_response.raise_for_status()
token_data = token_response.json()
with open("/tmp/edilberto_rotated_token", "w") as handle:
    handle.write(token_data.get("refresh_token", ""))
headers = {"Authorization": f"Bearer {token_data['access_token']}"}

now = datetime.now(TZ)
day_start = datetime.combine(now.date(), time.min, TZ)
day_end = day_start + timedelta(days=1)
date_from = day_start.isoformat(timespec="milliseconds")
date_to = day_end.isoformat(timespec="milliseconds")

orders = []
offset = 0
limit = 50
while True:
    response = requests.get(
        f"{API}/orders/search",
        headers=headers,
        params={
            "seller": SELLER_ID,
            "order.date_created.from": date_from,
            "order.date_created.to": date_to,
            "sort": "date_desc",
            "limit": limit,
            "offset": offset,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("results") or []
    orders.extend(rows)
    offset += len(rows)
    if not rows or offset >= int((data.get("paging") or {}).get("total") or 0):
        break

paid_orders = []
cancelled_orders = []
pending_orders = []
products = {}
for order in orders:
    status = order.get("status")
    tags = set(order.get("tags") or [])
    approved = any(
        payment.get("status") == "approved"
        for payment in (order.get("payments") or [])
    )
    if status in {"cancelled", "invalid"}:
        cancelled_orders.append(order)
        continue
    if status in {"paid", "partially_refunded"} or "paid" in tags or approved:
        paid_orders.append(order)
        for row in order.get("order_items") or []:
            item = row.get("item") or {}
            item_id = item.get("id") or "SIN_ID"
            quantity = int(row.get("quantity") or 0)
            unit_price = float(row.get("unit_price") or 0)
            entry = products.setdefault(item_id, {
                "item_id": item_id,
                "title": item.get("title") or "",
                "units": 0,
                "amount": 0.0,
            })
            entry["units"] += quantity
            entry["amount"] += unit_price * quantity
    else:
        pending_orders.append(order)

units = sum(row["units"] for row in products.values())
amount = round(sum(row["amount"] for row in products.values()), 2)
result = {
    "seller_id": SELLER_ID,
    "timezone": str(TZ),
    "generated_at": now.isoformat(),
    "date": str(now.date()),
    "paid_orders": len(paid_orders),
    "units": units,
    "sales_amount": amount,
    "cancelled_orders": len(cancelled_orders),
    "pending_orders": len(pending_orders),
    "products": sorted(
        products.values(), key=lambda row: (-row["amount"], row["title"])
    ),
}
print("DAILY_SALES=" + json.dumps(result, ensure_ascii=False), flush=True)
