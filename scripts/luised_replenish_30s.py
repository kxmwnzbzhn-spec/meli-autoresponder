#!/usr/bin/env python3
"""Mantiene exactamente 1 unidad visible en cuatro publicaciones autorizadas de LuisEd."""
import json
import os
import time
import requests
from stock_policy import item_stock_action

API = "https://api.mercadolibre.com"
ACCOUNT = "LUISED"
SELLER_ID = 3584846108
ITEMS = [
    "MLM3356000563",
    "MLM3356016605",
    "MLM3356013517",
    "MLM3355975897",
]
TICK = 30
DURATION = int(os.environ.get("RUN_DURATION_SEC", str(5 * 3600 + 30 * 60)))

def refresh():
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_LUISED"],
    }, timeout=20)
    r.raise_for_status()
    return r.json()

tok = refresh()
access_token = tok["access_token"]
rotated_refresh_token = tok.get("refresh_token", "")
H = {"Authorization": f"Bearer {access_token}"}
HJ = {**H, "Content-Type": "application/json"}

def inspect_and_replenish(item_id, initial=False):
    r = requests.get(f"{API}/items/{item_id}", headers=H, timeout=15)
    if r.status_code == 401:
        raise RuntimeError("access token expirado antes de completar el ciclo")
    r.raise_for_status()
    item = r.json()
    if item.get("seller_id") != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    if item.get("inventory_id"):
        raise RuntimeError(f"{item_id}: publicación Full/inventory; MELI controla su stock")
    if item.get("variations"):
        raise RuntimeError(f"{item_id}: tiene variaciones; requiere configuración individual")
    qty = int(item.get("available_quantity") or 0)
    status = item.get("status")
    title = item.get("title", "")
    action=item_stock_action(status,item.get("sub_status"),qty)
    if action == "skip_non_sellable":
        if initial:
            print(f"[POLICY-SKIP] {item_id} status={status} sub={item.get('sub_status')} qty={qty} title={title}",flush=True)
        return
    if action in ("set_quantity","replenish_out_of_stock"):
        body = {"available_quantity": 1}
        if action == "replenish_out_of_stock":
            body["status"] = "active"
        u = requests.put(f"{API}/items/{item_id}", headers=HJ, json=body, timeout=15)
        if u.status_code not in (200, 201):
            raise RuntimeError(f"{item_id}: PUT {u.status_code} {u.text[:300]}")
        updated = u.json()
        print(f"[REPLENISHED] {item_id} qty {qty}->1 status={status}->{updated.get('status')} sub={updated.get('sub_status')} title={title}", flush=True)
    elif initial:
        print(f"[OK] {item_id} active qty=1 title={title}", flush=True)

print(f"=== {ACCOUNT}: validación inicial de {len(ITEMS)} publicaciones ===", flush=True)
for iid in ITEMS:
    inspect_and_replenish(iid, initial=True)

started = time.time()
cycles = 0
while time.time() - started < DURATION:
    cycles += 1
    cycle_start = time.time()
    for iid in ITEMS:
        try:
            inspect_and_replenish(iid)
        except Exception as exc:
            print(f"[ERROR] {iid}: {exc}", flush=True)
    if cycles % 20 == 0:
        print(f"[HEARTBEAT] cycles={cycles} elapsed={int(time.time()-started)}s", flush=True)
    delay = TICK - (time.time() - cycle_start)
    if delay > 0:
        time.sleep(delay)

with open("/tmp/luised_rotated_token", "w") as fh:
    fh.write(rotated_refresh_token)
print(f"=== END cycles={cycles} ===", flush=True)

# Reinicio controlado para adoptar el refresh token vigente.
