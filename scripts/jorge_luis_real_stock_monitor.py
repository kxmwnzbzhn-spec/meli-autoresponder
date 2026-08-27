#!/usr/bin/env python3
"""Maintain one visible unit for Jorge Luis while respecting real stock limits."""
import os
import time
import requests
from stock_policy import item_stock_action

API = "https://api.mercadolibre.com"
SELLER_ID = 3640697853
TIMEOUT = 30
TICK = 30
DURATION = int(os.environ.get("RUN_DURATION_SEC", "19800"))

REAL_STOCK_LIMITS = {
    # Source MLM6061793370: 16 initial - 10 paid before migration.
    "MLM6098727716": 6,
    # Source MLM6061793358: 28 initial - 10 paid before migration.
    "MLM3402386723": 18,
    # Sources MLM6075579250 (1) + MLM3386065727 (0), same catalog.
    "MLM3402363017": 1,
    # Source MLM6061831150: 28 initial - 3 paid before migration.
    "MLM3402390259": 25,
    # Source MLM6075598700: one verified editable unit at migration.
    "MLM6099889822": 1,
    # Exhausted sources cloned as paused/under-review catalog listings.
    "MLM6100157520": 0,  # Source MLM6075595766
    "MLM6100158830": 0,  # Source MLM3387189275
    "MLM6100171026": 0,  # Source MLM6075580366
    "MLM3403250729": 0,  # Source MLM6075497680
    "MLM3403240547": 0,  # Source MLM6075502880
    "MLM3403241131": 0,  # Source MLM6075597440
}

# Explicitly authorized for continuous one-visible-unit replenishment
# without a physical inventory ceiling.
UNCAPPED_ITEMS = {
    "MLM6100171026",
    "MLM6100158830",
    "MLM3403250729",
    "MLM3403240547",
    "MLM3403241131",
    "MLM6097042780",
    "MLM3401279297",
    "MLM6097051040",
    "MLM6097038456",
    "MLM6097051428",
    "MLM3401288599",
    "MLM6097030480",
    "MLM3401292527",
    "MLM3401303117",
}

FORCE_ACTIVE_ITEMS = {
    "MLM6100171026",
    "MLM6100158830",
    "MLM3403250729",
    "MLM3403240547",
    "MLM3403241131",
}

ALL_MONITORED_ITEMS = tuple(REAL_STOCK_LIMITS) + tuple(UNCAPPED_ITEMS)

r = requests.post(
    f"{API}/oauth/token",
    data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"],
    },
    timeout=TIMEOUT,
)
r.raise_for_status()
data = r.json()
with open("/tmp/jorge_luis_rotated_token", "w") as handle:
    handle.write(data.get("refresh_token", ""))
H = {"Authorization": f"Bearer {data['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}


def get_item(item_id):
    response = requests.get(f"{API}/items/{item_id}", headers=H, timeout=TIMEOUT)
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    return item


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


def enforce(item_id, initial=False):
    limit = REAL_STOCK_LIMITS.get(item_id)
    sold = paid_units(item_id) if limit is not None else None
    remaining = max(0, limit - sold) if limit is not None else None
    item = get_item(item_id)

    if item_id in FORCE_ACTIVE_ITEMS:
        if item.get("status") == "active" and int(item.get("available_quantity") or 0) == 1:
            if initial:
                print(f"[FORCE-ACTIVE-OK] {item_id} qty=1", flush=True)
            return
        response = requests.put(
            f"{API}/items/{item_id}",
            headers=HJ,
            json={"available_quantity": 1, "status": "active"},
            timeout=TIMEOUT,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"{item_id}: force-active {response.status_code} "
                f"{response.text[:500]}"
            )
        final = get_item(item_id)
        if final.get("status") != "active" or int(final.get("available_quantity") or 0) != 1:
            raise RuntimeError(
                f"{item_id}: force-active verification "
                f"status={final.get('status')} qty={final.get('available_quantity')}"
            )
        print(f"[FORCE-ACTIVATED] {item_id} qty=1", flush=True)
        return

    action = item_stock_action(
        item.get("status"),
        item.get("sub_status"),
        item.get("available_quantity"),
    )
    if initial or (remaining is not None and remaining <= 2):
        policy = "real-stock" if limit is not None else "continuous-uncapped"
        print(
            f"[STOCK] {item_id} policy={policy} initial={limit} sold={sold} "
            f"remaining={remaining} status={item.get('status')} "
            f"qty={item.get('available_quantity')}",
            flush=True,
        )

    if remaining is not None and remaining <= 0:
        if item.get("status") == "active":
            response = requests.put(
                f"{API}/items/{item_id}",
                headers=HJ,
                json={"status": "paused"},
                timeout=TIMEOUT,
            )
            if response.status_code not in (200, 201):
                raise RuntimeError(
                    f"{item_id}: pause {response.status_code} {response.text[:400]}"
                )
            print(f"[PAUSED-EXHAUSTED] {item_id}", flush=True)
        return

    if action == "noop":
        return
    if action == "skip_non_sellable":
        print(
            f"[POLICY-SKIP] {item_id} status={item.get('status')} "
            f"sub={item.get('sub_status')}",
            flush=True,
        )
        return

    body = {"available_quantity": 1}
    if action == "replenish_out_of_stock":
        body["status"] = "active"
    response = requests.put(
        f"{API}/items/{item_id}",
        headers=HJ,
        json=body,
        timeout=TIMEOUT,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{item_id}: replenish {response.status_code} {response.text[:500]}"
        )
    final = get_item(item_id)
    if final.get("status") != "active" or int(final.get("available_quantity") or 0) != 1:
        raise RuntimeError(
            f"{item_id}: verificación status={final.get('status')} "
            f"qty={final.get('available_quantity')}"
        )
    print(f"[REPLENISHED] {item_id} remaining={remaining} qty=1", flush=True)


print("=== JORGE_LUIS stock monitor: initial validation ===", flush=True)
for item_id in ALL_MONITORED_ITEMS:
    try:
        enforce(item_id, initial=True)
    except Exception as exc:
        print(f"[ERROR] {item_id}: {exc}", flush=True)

started = time.time()
cycles = 0
while time.time() - started < DURATION:
    cycles += 1
    cycle_start = time.time()
    for item_id in ALL_MONITORED_ITEMS:
        try:
            enforce(item_id)
        except Exception as exc:
            print(f"[ERROR] {item_id}: {exc}", flush=True)
    delay = TICK - (time.time() - cycle_start)
    if delay > 0:
        time.sleep(delay)
print(f"=== END cycles={cycles} ===", flush=True)
