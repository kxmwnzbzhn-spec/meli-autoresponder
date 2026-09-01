#!/usr/bin/env python3
"""Corte histórico de bocinas ROCIOANGEL con devolución fija de $140 compartida."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

API = "https://api.mercadolibre.com"
TZ = ZoneInfo("America/Mexico_City")
TIMEOUT = 30
FLAT_RETURN_COST = 140.0
START = datetime(2026, 1, 1, tzinfo=TZ)


def num(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def is_speaker(title):
    text = (title or "").lower().replace("-", " ")
    return any(key in text for key in (
        "bocina", "altavoz", "parlante", "speaker", "jbl go", "jblgo",
        "marshall", "willen", "emberton", "sony srs", "srs xb",
    ))


def unit_cost(title):
    text = (title or "").lower().replace("-", " ")
    if "go 5" in text or "go5" in text:
        return 280.0, "GO5"
    if "go 4" in text or "go4" in text:
        return 233.0, "GO4"
    if "sony" in text or "srs xb" in text or "srsxb" in text:
        return 320.0, "SONY"
    if "willen" in text:
        return 320.0, "WILLEN"
    if "emberton" in text:
        return 430.0, "EMBERTON"
    return None, "UNKNOWN"


auth = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": "2008666770714005",
        "client_secret": os.environ["MELI_APP_SECRET"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"],
    },
    timeout=TIMEOUT,
)
auth.raise_for_status()
token_data = auth.json()
with open("/tmp/rocio_partner_cut_rotated", "w") as handle:
    handle.write(token_data.get("refresh_token", ""))
HEADERS = {"Authorization": f"Bearer {token_data['access_token']}"}


def api_get(url, params=None):
    for attempt in range(8):
        response = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()
        time.sleep(min(12, 2 + attempt * 2))
    response.raise_for_status()


seller = int(api_get(f"{API}/users/me")["id"])
now = datetime.now(TZ)

orders = []
offset = 0
while True:
    data = api_get(
        f"{API}/orders/search",
        params={
            "seller": seller,
            "order.date_created.from": START.isoformat(timespec="milliseconds"),
            "order.date_created.to": now.isoformat(timespec="milliseconds"),
            "sort": "date_asc",
            "limit": 50,
            "offset": offset,
        },
    )
    batch = data.get("results") or []
    orders.extend(batch)
    offset += len(batch)
    if not batch or offset >= int((data.get("paging") or {}).get("total") or 0):
        break

selected = {}
for order in orders:
    if order.get("status") in {"cancelled", "invalid"}:
        continue
    tags = set(order.get("tags") or [])
    payments = order.get("payments") or []
    is_paid = (
        order.get("status") in {"paid", "partially_refunded"}
        or "paid" in tags
        or any(p.get("status") in {"approved", "refunded", "charged_back"} for p in payments)
    )
    if not is_paid:
        continue
    speaker_items = [
        item for item in (order.get("order_items") or [])
        if is_speaker((item.get("item") or {}).get("title"))
    ]
    if speaker_items:
        selected[int(order["id"])] = (order, speaker_items)


def order_external(pair):
    order_id, (order, speaker_items) = pair
    all_items = order.get("order_items") or []
    speaker_gross = sum(num(i.get("unit_price")) * int(i.get("quantity") or 0) for i in speaker_items)
    order_gross = sum(num(i.get("unit_price")) * int(i.get("quantity") or 0) for i in all_items)
    share = speaker_gross / order_gross if order_gross else 0.0
    shipping_id = (order.get("shipping") or {}).get("id")
    outbound = 0.0
    shipping_http = None
    if shipping_id:
        try:
            costs = api_get(f"{API}/shipments/{shipping_id}/costs")
            shipping_http = 200
            senders = costs.get("senders") or []
            matched = False
            for sender in senders:
                if str(sender.get("user_id")) == str(seller):
                    outbound += num(sender.get("cost"))
                    matched = True
            if not matched and len(senders) == 1:
                outbound += num(senders[0].get("cost"))
        except Exception as exc:
            shipping_http = str(exc)[:180]
    refunded = sum(
        num(payment.get("transaction_amount_refunded"))
        or (
            num(payment.get("transaction_amount"))
            if payment.get("status") in {"refunded", "charged_back"}
            else 0.0
        )
        for payment in (order.get("payments") or [])
    )
    return order_id, {
        "share": share,
        "outbound": outbound * share,
        "refund": refunded * share,
        "shipping_http": shipping_http,
    }


external = {}
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = [pool.submit(order_external, pair) for pair in selected.items()]
    for future in as_completed(futures):
        order_id, data = future.result()
        external[order_id] = data

claims = []
offset = 0
date_range = (
    f"date_created:after:{START.isoformat(timespec='milliseconds')},"
    f"before:{now.isoformat(timespec='milliseconds')}"
)
while True:
    data = api_get(
        f"{API}/post-purchase/v1/claims/search",
        params={
            "players.user_id": seller,
            "players.role": "respondent",
            "range": date_range,
            "limit": 50,
            "offset": offset,
        },
    )
    batch = data.get("data") or []
    claims.extend(batch)
    offset += len(batch)
    if not batch or offset >= int((data.get("paging") or {}).get("total") or 0):
        break

speaker_claims = [
    claim for claim in claims
    if claim.get("resource") == "order"
    and int(claim.get("resource_id") or 0) in selected
]


def real_return(claim):
    related = claim.get("related_entities") or []
    related_text = " ".join(str(value).lower() for value in related)
    return claim.get("type") == "returns" or "return" in related_text


return_claims = [claim for claim in speaker_claims if real_return(claim)]
return_order_ids = sorted({int(claim.get("resource_id")) for claim in return_claims})

gross = 0.0
fees = 0.0
taxes = 0.0
cogs = 0.0
units = 0
first_sale = None
unknown = []
products = {}
order_costs = {}
order_gross = {}
order_units = {}
order_titles = {}

for order_id, (order, items) in selected.items():
    date_created = order.get("date_created")
    if first_sale is None or date_created < first_sale:
        first_sale = date_created
    order_costs[order_id] = 0.0
    order_gross[order_id] = 0.0
    order_units[order_id] = 0
    order_titles[order_id] = []
    for line in items:
        item = line.get("item") or {}
        title = item.get("title") or ""
        item_id = item.get("id") or "SIN_ID"
        quantity = int(line.get("quantity") or 0)
        line_gross = num(line.get("unit_price")) * quantity
        cost, kind = unit_cost(title)
        units += quantity
        gross += line_gross
        fees += num(line.get("sale_fee"))
        order_gross[order_id] += line_gross
        order_units[order_id] += quantity
        order_titles[order_id].append(title)
        product = products.setdefault(item_id, {
            "item_id": item_id,
            "title": title,
            "kind": kind,
            "units": 0,
            "gross": 0.0,
            "unit_cost": cost,
        })
        product["units"] += quantity
        product["gross"] += line_gross
        if cost is None:
            unknown.append({"item_id": item_id, "title": title, "units": quantity})
        else:
            line_cost = cost * quantity
            cogs += line_cost
            order_costs[order_id] += line_cost
    taxes += num((order.get("taxes") or {}).get("amount")) * external[order_id]["share"]

outbound_total = sum(value["outbound"] for value in external.values())
refunds = sum(value["refund"] for value in external.values())

# El producto reembolsado vuelve a inventario: se excluye proporcionalmente del
# costo consumido. La pérdida adicional fija se divide vía utilidad.
returned_cogs = 0.0
for order_id in return_order_ids:
    line_gross = order_gross.get(order_id, 0.0)
    refund = external.get(order_id, {}).get("refund", 0.0)
    ratio = min(1.0, refund / line_gross) if line_gross else 0.0
    returned_cogs += order_costs.get(order_id, 0.0) * ratio

net_sold_cogs = max(0.0, cogs - returned_cogs)
return_count = len(return_order_ids)
flat_return_total = return_count * FLAT_RETURN_COST
platform_net = gross - fees - outbound_total - taxes - refunds
profit_after_returns = platform_net - net_sold_cogs - flat_return_total
partner_due = profit_after_returns / 2.0
owner_due = net_sold_cogs + profit_after_returns / 2.0

claims_by_order = {}
for claim in return_claims:
    order_id = int(claim.get("resource_id"))
    claims_by_order.setdefault(order_id, []).append(claim)

return_details = []
for order_id in return_order_ids:
    order_claims = claims_by_order.get(order_id, [])
    return_details.append({
        "order_id": order_id,
        "claim_ids": [claim.get("id") for claim in order_claims],
        "statuses": sorted({str(claim.get("status") or "") for claim in order_claims}),
        "reasons": sorted({str(claim.get("reason_id") or claim.get("type") or "") for claim in order_claims}),
        "titles": sorted(set(order_titles.get(order_id, []))),
        "units_in_order": order_units.get(order_id, 0),
        "refund": round(external.get(order_id, {}).get("refund", 0.0), 2),
        "warehouse_action": "PEDIR PRODUCTO DE VUELTA",
    })

result = {
    "seller_id": seller,
    "from": first_sale,
    "to": now.isoformat(),
    "speaker_orders": len(selected),
    "speaker_units": units,
    "gross": round(gross, 2),
    "commissions": round(fees, 2),
    "outbound_shipping": round(outbound_total, 2),
    "taxes": round(taxes, 2),
    "refunds": round(refunds, 2),
    "net_product_cost_after_returns": round(net_sold_cogs, 2),
    "returned_product_cost_removed": round(returned_cogs, 2),
    "real_return_count": return_count,
    "return_cost_each": FLAT_RETURN_COST,
    "flat_return_cost_total": round(flat_return_total, 2),
    "return_cost_each_partner": round(flat_return_total / 2.0, 2),
    "profit_after_all_costs": round(profit_after_returns, 2),
    "partner_due": round(partner_due, 2),
    "owner_due": round(owner_due, 2),
    "unknown_cost_products": unknown,
    "shipment_errors": [
        {"order_id": order_id, "error": value["shipping_http"]}
        for order_id, value in external.items()
        if value["shipping_http"] not in (None, 200)
    ],
    "return_details": return_details,
    "products": sorted(products.values(), key=lambda product: -product["gross"]),
}
print("ROCIO_PARTNER_CUT_140=" + json.dumps(result, ensure_ascii=False), flush=True)
