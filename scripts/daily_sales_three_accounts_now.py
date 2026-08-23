#!/usr/bin/env python3
"""Corte diario en vivo para Luis Eduardo, Edilberto y ASVA E."""
import json
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

API = "https://api.mercadolibre.com"
TIMEOUT = 30
TZ = ZoneInfo("America/Mexico_City")
ACCOUNTS = [
    ("LUISED", 3584846108, "MELI_REFRESH_TOKEN_LUISED", "MELI_APP_ID_NEW", "MELI_APP_SECRET_NEW", "/tmp/luised_rotated_token"),
    ("EDILBERTO", 3616975257, "MELI_REFRESH_TOKEN_EDILBERTO", "MELI_APP_ID_NEW", "MELI_APP_SECRET_NEW", "/tmp/edilberto_rotated_token"),
    ("ASVA_E", 1668713481, "MELI_REFRESH_TOKEN_ASVA", "MELI_APP_ID", "MELI_APP_SECRET", "/tmp/asva_rotated_token"),
]

def refresh(secret_name, app_id_name, app_secret_name, output_path):
    response = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ[app_id_name],
            "client_secret": os.environ[app_secret_name],
            "refresh_token": os.environ[secret_name],
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    with open(output_path, "w") as handle:
        handle.write(data.get("refresh_token", ""))
    return data["access_token"]

def report_account(name, seller_id, token, date_from, date_to):
    headers = {"Authorization": f"Bearer {token}"}
    orders = []
    offset = 0
    limit = 50
    while True:
        response = requests.get(
            f"{API}/orders/search",
            headers=headers,
            params={
                "seller": seller_id,
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

    paid_orders, cancelled, pending = [], [], []
    products = {}
    for order in orders:
        status = order.get("status")
        tags = set(order.get("tags") or [])
        approved = any(p.get("status") == "approved" for p in (order.get("payments") or []))
        if status in {"cancelled", "invalid"}:
            cancelled.append(order)
            continue
        if status in {"paid", "partially_refunded"} or "paid" in tags or approved:
            paid_orders.append(order)
            for row in order.get("order_items") or []:
                item = row.get("item") or {}
                item_id = item.get("id") or "SIN_ID"
                quantity = int(row.get("quantity") or 0)
                amount = float(row.get("unit_price") or 0) * quantity
                product = products.setdefault(item_id, {
                    "item_id": item_id,
                    "title": item.get("title") or "",
                    "units": 0,
                    "amount": 0.0,
                })
                product["units"] += quantity
                product["amount"] += amount
        else:
            pending.append(order)

    for product in products.values():
        product["amount"] = round(product["amount"], 2)
    return {
        "account": name,
        "seller_id": seller_id,
        "paid_orders": len(paid_orders),
        "units": sum(p["units"] for p in products.values()),
        "sales_amount": round(sum(p["amount"] for p in products.values()), 2),
        "cancelled_orders": len(cancelled),
        "pending_orders": len(pending),
        "products": sorted(products.values(), key=lambda row: (-row["amount"], row["title"])),
    }

now = datetime.now(TZ)
start = datetime.combine(now.date(), time.min, TZ)
end = start + timedelta(days=1)
results = []
for name, seller_id, secret_name, app_id_name, app_secret_name, output_path in ACCOUNTS:
    token = refresh(secret_name, app_id_name, app_secret_name, output_path)
    results.append(report_account(
        name, seller_id, token,
        start.isoformat(timespec="milliseconds"),
        end.isoformat(timespec="milliseconds"),
    ))

output = {
    "date": str(now.date()),
    "generated_at": now.isoformat(),
    "timezone": str(TZ),
    "accounts": results,
    "combined": {
        "paid_orders": sum(r["paid_orders"] for r in results),
        "units": sum(r["units"] for r in results),
        "sales_amount": round(sum(r["sales_amount"] for r in results), 2),
        "cancelled_orders": sum(r["cancelled_orders"] for r in results),
        "pending_orders": sum(r["pending_orders"] for r in results),
    },
}
print("THREE_DAILY_SALES=" + json.dumps(output, ensure_ascii=False), flush=True)
