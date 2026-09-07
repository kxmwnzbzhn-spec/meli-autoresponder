#!/usr/bin/env python3
"""ROSA MARIA: keep one unit visible with unlimited automatic restock."""
import json
import os
import time

import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3658310023
TIMEOUT = 30
TICK = 30
DURATION = int(os.environ.get("RUN_DURATION_SEC", "19800"))

with open("config/rosa_maria_autostock_unlimited.json", encoding="utf-8") as stream:
    ITEM_IDS = list(dict.fromkeys(json.load(stream)))


def exchange_token():
    response = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["MELI_APP_ID"],
            "client_secret": os.environ["MELI_APP_SECRET"],
            "refresh_token": os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"],
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    with open("/tmp/rosa_maria_rotated_token", "w", encoding="utf-8") as stream:
        stream.write(payload.get("refresh_token", ""))
    return payload["access_token"]


ACCESS_TOKEN = exchange_token()
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
JSON_HEADERS = {**HEADERS, "Content-Type": "application/json"}

account = requests.get(f"{API}/users/me", headers=HEADERS, timeout=TIMEOUT)
account.raise_for_status()
if int(account.json().get("id") or 0) != SELLER_ID:
    raise RuntimeError("El token no corresponde a ROSA MARIA")


def get_item(item_id):
    response = requests.get(
        f"{API}/items/{item_id}", headers=HEADERS, timeout=TIMEOUT
    )
    response.raise_for_status()
    item = response.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: pertenece a otro vendedor")
    return item


def replenish(item_id, initial=False):
    item = get_item(item_id)
    status = item.get("status")
    quantity = int(item.get("available_quantity") or 0)
    if initial:
        print(
            f"[STOCK] {item_id} unlimited status={status} qty={quantity}",
            flush=True,
        )
    if status == "active" and quantity == 1:
        return
    if status not in {"active", "paused"}:
        print(
            f"[POLICY-SKIP] {item_id} status={status} sub={item.get('sub_status')}",
            flush=True,
        )
        return
    body = {"available_quantity": 1}
    if status == "paused":
        body["status"] = "active"
    response = requests.put(
        f"{API}/items/{item_id}",
        headers=JSON_HEADERS,
        json=body,
        timeout=TIMEOUT,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{item_id}: stock HTTP {response.status_code} {response.text[:500]}"
        )
    verified = get_item(item_id)
    if (
        verified.get("status") != "active"
        or int(verified.get("available_quantity") or 0) != 1
    ):
        raise RuntimeError(
            f"{item_id}: verificacion status={verified.get('status')} "
            f"qty={verified.get('available_quantity')}"
        )
    print(f"[REPLENISHED] {item_id} unlimited qty=1", flush=True)


for item_id in ITEM_IDS:
    replenish(item_id, initial=True)

started = time.time()
cycles = 0
while time.time() - started < DURATION:
    cycles += 1
    cycle_started = time.time()
    for item_id in ITEM_IDS:
        try:
            replenish(item_id)
        except Exception as error:
            print(f"[ERROR-STOCK] {item_id}: {error}", flush=True)
    time.sleep(max(0, TICK - (time.time() - cycle_started)))

print(f"[END] cycles={cycles} items={len(ITEM_IDS)}", flush=True)
