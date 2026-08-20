#!/usr/bin/env python3
"""Mantiene una unidad visible en las dos publicaciones autorizadas de Edilberto.
Validado para ejecución continua cada 30 segundos y prueba inicial controlada.
"""
import os
import time
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
TARGETS = ["MLMU4851933870", "MLM3355626501"]
FALLBACK_ITEMS = {
    "MLMU4851933870": ["MLM3355625791", "MLM3355650889"],
    "MLMU4821841613": ["MLM3355626501"],
}
TICK = 30
DURATION = int(os.environ.get("RUN_DURATION_SEC", str(5 * 3600 + 30 * 60)))

def refresh():
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    }, timeout=20)
    r.raise_for_status()
    return r.json()

tok = refresh()
with open("/tmp/edilberto_rotated_token", "w") as fh:
    fh.write(tok.get("refresh_token", ""))
H = {"Authorization": f"Bearer {tok['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}

def get_stock(upid):
    r = requests.get(f"{API}/user-products/{upid}/stock", headers=H, timeout=15)
    if r.status_code != 200:
        return None, None, r
    return r.json(), r.headers.get("x-version"), r

def keep_one_user_product(upid, initial=False):
    stock, version, raw = get_stock(upid)
    if stock is None:
        raise RuntimeError(f"{upid}: stock GET {raw.status_code} {raw.text[:250]}")
    if int(stock.get("user_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{upid}: user_id inesperado {stock.get('user_id')}")
    locations = stock.get("locations") or []
    editable = [x for x in locations if x.get("type") != "meli_facility"]
    if not editable:
        raise RuntimeError(f"{upid}: solo tiene stock Full; MELI controla sus existencias")
    total = sum(int(x.get("quantity") or 0) for x in editable)
    kinds = sorted({x.get("type") for x in editable})
    if total == 1:
        if initial:
            print(f"[OK-UP] {upid} editable_qty=1 types={kinds}", flush=True)
        return
    if len(kinds) != 1:
        raise RuntimeError(f"{upid}: tipos editables mixtos {kinds}")
    kind = kinds[0]
    keeper = max(range(len(editable)), key=lambda i: int(editable[i].get("quantity") or 0))
    headers = dict(HJ)
    if version:
        headers["x-version"] = version
    url = f"{API}/user-products/{upid}/stock/type/{kind}"
    if kind == "seller_warehouse":
        out = []
        for i, loc in enumerate(editable):
            row = {"quantity": 1 if i == keeper else 0}
            if loc.get("store_id") is not None:
                row["store_id"] = loc.get("store_id")
            if loc.get("network_node_id") is not None:
                row["network_node_id"] = loc.get("network_node_id")
            out.append(row)
        body = {"locations": out}
    elif kind == "selling_address":
        body = {"quantity": 1}
    else:
        raise RuntimeError(f"{upid}: tipo de stock no soportado {kind}")
    u = requests.put(url, headers=headers, json=body, timeout=15)
    if u.status_code not in (200, 201, 204):
        blocked = u.status_code == 400 and "blocked for modifications to the selling address" in u.text
        fallback = FALLBACK_ITEMS.get(upid) or []
        if not blocked or not fallback:
            raise RuntimeError(f"{upid}: stock PUT {u.status_code} {u.text[:300]}")
        repaired = []
        for iid in fallback:
            current = requests.get(f"{API}/items/{iid}", headers=H, timeout=15).json()
            item_body = {"available_quantity": 1}
            if current.get("status") == "paused":
                item_body["status"] = "active"
            ri = requests.put(f"{API}/items/{iid}", headers=HJ, json=item_body, timeout=15)
            if ri.status_code not in (200, 201):
                raise RuntimeError(f"{upid}/{iid}: fallback PUT {ri.status_code} {ri.text[:300]}")
            repaired.append(iid)
        verify, _, _ = get_stock(upid)
        new_total = sum(int(x.get("quantity") or 0) for x in (verify.get("locations") or []) if x.get("type") != "meli_facility")
        if new_total != 1:
            raise RuntimeError(f"{upid}: fallback ejecutado pero qty verificada={new_total}")
        print(f"[REPLENISHED-ITEM-FALLBACK] {upid} editable_qty {total}->1 items={repaired}", flush=True)
        return
    print(f"[REPLENISHED-UP] {upid} editable_qty {total}->1 type={kind}", flush=True)

def keep_one_item(item_id, initial=False):
    r = requests.get(f"{API}/items/{item_id}", headers=H, timeout=15)
    r.raise_for_status()
    item = r.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    upid = item.get("user_product_id")
    if upid:
        stock, _, raw = get_stock(upid)
        if stock is not None and any(x.get("type") != "meli_facility" for x in (stock.get("locations") or [])):
            keep_one_user_product(upid, initial=initial)
            if item.get("status") == "paused":
                u = requests.put(f"{API}/items/{item_id}", headers=HJ, json={"status": "active"}, timeout=15)
                if u.status_code not in (200, 201):
                    raise RuntimeError(f"{item_id}: reactivar {u.status_code} {u.text[:250]}")
                print(f"[REACTIVATED] {item_id}", flush=True)
            return
    if item.get("inventory_id"):
        raise RuntimeError(f"{item_id}: publicación Full; MELI controla sus existencias")
    if item.get("variations"):
        raise RuntimeError(f"{item_id}: tiene variaciones; requiere configuración individual")
    qty = int(item.get("available_quantity") or 0)
    status = item.get("status")
    if qty == 1 and status == "active":
        if initial:
            print(f"[OK] {item_id} active qty=1 title={item.get('title','')}", flush=True)
        return
    body = {"available_quantity": 1}
    if status == "paused":
        body["status"] = "active"
    u = requests.put(f"{API}/items/{item_id}", headers=HJ, json=body, timeout=15)
    if u.status_code not in (200, 201):
        raise RuntimeError(f"{item_id}: PUT {u.status_code} {u.text[:300]}")
    updated = u.json()
    print(f"[REPLENISHED] {item_id} qty {qty}->1 status={status}->{updated.get('status')} title={item.get('title','')}", flush=True)

def check(target, initial=False):
    if target.startswith("MLMU"):
        keep_one_user_product(target, initial=initial)
    else:
        keep_one_item(target, initial=initial)

print("=== EDILBERTO: validación inicial de 2 publicaciones ===", flush=True)
for target in TARGETS:
    check(target, initial=True)

started = time.time()
cycles = 0
while time.time() - started < DURATION:
    cycles += 1
    cycle_start = time.time()
    for target in TARGETS:
        try:
            check(target)
        except Exception as exc:
            print(f"[ERROR] {target}: {exc}", flush=True)
    if cycles % 20 == 0:
        print(f"[HEARTBEAT] cycles={cycles} elapsed={int(time.time()-started)}s", flush=True)
    delay = TICK - (time.time() - cycle_start)
    if delay > 0:
        time.sleep(delay)
print(f"=== END cycles={cycles} ===", flush=True)
