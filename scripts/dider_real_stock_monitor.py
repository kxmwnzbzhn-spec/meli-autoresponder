#!/usr/bin/env python3
"""DIDER: keep one unit visible with unlimited automatic replenishment."""
import os, time, requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3654003391
TIMEOUT = 30
TICK = 30
DURATION = int(os.environ.get("RUN_DURATION_SEC", "19800"))
ITEM_IDS = [
    "MLM3442582695",
    "MLM3442582711",
    "MLM3442595743",
    "MLM3442595765",
    "MLM3442595771",
]

r = requests.post(f"{API}/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_DIDER"],
}, timeout=TIMEOUT)
r.raise_for_status()
tok = r.json()
with open("/tmp/dider_rotated_token", "w") as h:
    h.write(tok.get("refresh_token", ""))
H = {"Authorization": f"Bearer {tok['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}

me = requests.get(f"{API}/users/me", headers=H, timeout=TIMEOUT)
me.raise_for_status()
if int(me.json().get("id") or 0) != SELLER_ID:
    raise RuntimeError(f"Cuenta incorrecta: {me.json().get('id')}")

def item(iid):
    q = requests.get(f"{API}/items/{iid}", headers=H, timeout=TIMEOUT)
    q.raise_for_status()
    d = q.json()
    if int(d.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{iid}: seller inesperado")
    return d

def enforce(iid, initial=False):
    d = item(iid)
    status = d.get("status")
    qty = int(d.get("available_quantity") or 0)
    if initial:
        print(f"[STOCK] {iid} unlimited status={status} qty={qty}", flush=True)
    if status == "active" and qty == 1:
        return
    if status not in {"active", "paused"}:
        print(f"[POLICY-SKIP] {iid} status={status} sub={d.get('sub_status')}", flush=True)
        return
    body = {"available_quantity": 1}
    if status == "paused":
        body["status"] = "active"
    u = requests.put(f"{API}/items/{iid}", headers=HJ, json=body, timeout=TIMEOUT)
    if u.status_code not in (200, 201):
        raise RuntimeError(f"{iid}: replenish HTTP {u.status_code} {u.text[:500]}")
    final = item(iid)
    if final.get("status") != "active" or int(final.get("available_quantity") or 0) != 1:
        raise RuntimeError(f"{iid}: verification status={final.get('status')} qty={final.get('available_quantity')}")
    print(f"[REPLENISHED] {iid} unlimited qty=1", flush=True)

for iid in ITEM_IDS:
    enforce(iid, initial=True)
started = time.time()
cycles = 0
while time.time() - started < DURATION:
    cycles += 1
    cycle = time.time()
    for iid in ITEM_IDS:
        try:
            enforce(iid)
        except Exception as exc:
            print(f"[ERROR] {iid}: {exc}", flush=True)
    time.sleep(max(0, TICK - (time.time() - cycle)))
print(f"[END] cycles={cycles}", flush=True)
