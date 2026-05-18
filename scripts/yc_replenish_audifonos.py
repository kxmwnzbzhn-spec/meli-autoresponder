#!/usr/bin/env python3
"""
YC seller — auto-replenish bot.
Mantiene qty=1 visible en Meli mientras descuenta de stock real local.
Stock real persistido en stock_yc_audifonos.json.
Loop: cada SLEEP segundos, N ITERATIONS por run.
"""
import os, time, requests, json

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
STOCK_FILE = "scripts/stock_yc_audifonos.json"

# items que monitoreamos en esta cuenta (visible qty cap, real stock se descuenta)
ITEMS_CAP = {
    "MLM2940664057": 1,  # Audífonos Bluetooth In-Ear Negro · visible siempre = 1
}

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }, timeout=20).json()
    return r["access_token"]

def load_real_stock():
    try:
        with open(STOCK_FILE) as f: return json.load(f)
    except: return {}

def save_real_stock(d):
    with open(STOCK_FILE,"w") as f: json.dump(d, f, indent=2)

def replenish_pass(H):
    real = load_real_stock()
    changed = False
    for iid, cap in ITEMS_CAP.items():
        rs = real.get(iid, 0)
        # Get current status + qty
        r = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=available_quantity,status",
                         headers=H, timeout=10)
        if r.status_code != 200:
            print(f"  ❌ {iid} read: {r.status_code} {r.text[:100]}"); continue
        d = r.json(); qty = d.get("available_quantity", 0); status = d.get("status")

        if rs <= 0:
            print(f"  ⏸️  {iid} sin stock real (0) — no reabastecer | visible qty={qty}")
            continue

        # Caso 1: item paused → reactivar + qty=cap
        if status == "paused":
            body = {"status":"active","available_quantity":cap}
            rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json=body, timeout=15)
            if rp.status_code == 200:
                real[iid] = rs - cap
                print(f"  ▶️  {iid} reactivado | real: {rs}→{real[iid]} | visible: {qty}→{cap}")
                changed = True
            else:
                print(f"  ❌ {iid} reactivate {rp.status_code}: {rp.text[:120]}")
            continue

        # Caso 2: active con qty < cap → subir a cap
        if status == "active" and qty < cap:
            rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                              json={"available_quantity":cap}, timeout=15)
            if rp.status_code == 200:
                diff = cap - qty
                real[iid] = rs - diff
                print(f"  🔢 {iid} qty {qty}→{cap} | real: {rs}→{real[iid]}")
                changed = True
            else:
                print(f"  ❌ {iid} replenish {rp.status_code}: {rp.text[:120]}")

    if changed: save_real_stock(real)
    return real

# Loop
TOKEN = get_token()
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
print(f"YC user: {me.get('nickname')} ({me.get('id')})")

ITER = int(os.environ.get("LOOP_ITERATIONS","10"))
SLEEP = int(os.environ.get("LOOP_SLEEP","30"))

for i in range(ITER):
    print(f"\n=== Iter {i+1}/{ITER} | {time.strftime('%H:%M:%S')} ===")
    try:
        real = replenish_pass(H)
        print(f"Stock real restante: {real}")
    except Exception as e:
        print(f"err: {e}")
        try: TOKEN = get_token(); H = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
        except: pass
    if i < ITER-1: time.sleep(SLEEP)
