#!/usr/bin/env python3
"""Wilbert: reactivar items pausados + mantener qty=1 visible. Loop 10×30s."""
import os, time, requests, json

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_WILBERT"]

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    return r["access_token"]

def replenish_pass(H, USER_ID):
    """Una pasada: reactivar todos los pausados + asegurar qty=1 visible."""
    try: cfg = json.load(open("stock_config_wilbert.json"))
    except: cfg = {}

    # 1. Listar pausados
    paused_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        paused_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

    # 2. Reactivar pausados con stock disponible
    reactivated = 0
    for iid in paused_ids:
        if iid not in cfg:
            continue
        item_cfg = cfg[iid]
        if not item_cfg.get("auto_replenish", False): continue
        if not item_cfg.get("active", True): continue

        real_stock = item_cfg.get("real_stock", 0)
        if real_stock <= 0:
            print(f"  ⏸️  {iid} sin stock real → no reactivar")
            continue

        body = {"status":"active","available_quantity":1}
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
        if rp.status_code == 200:
            reactivated += 1
            cfg[iid]["real_stock"] = real_stock - 1
            print(f"  ▶️  {iid} reactivado (real_stock {real_stock}→{real_stock-1})")
        else:
            print(f"  ❌ {iid} {rp.status_code}: {rp.text[:120]}")

    # 3. Listar activos con qty=0 → subirlos a 1 si hay stock
    active_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        active_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

    qty_fixed = 0
    for iid in active_ids:
        if iid not in cfg: continue
        item_cfg = cfg[iid]
        if not item_cfg.get("auto_replenish",False): continue

        gg = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=available_quantity,status",headers=H,timeout=10).json()
        qty = gg.get("available_quantity",0)
        st = gg.get("status","")
        if qty < 1 and st == "active":
            real_stock = item_cfg.get("real_stock",0)
            if real_stock > 0:
                rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":1},timeout=15)
                if rp.status_code == 200:
                    qty_fixed += 1
                    cfg[iid]["real_stock"] = real_stock - 1
                    print(f"  🔢 {iid} qty 0→1 (real_stock {real_stock}→{real_stock-1})")

    if reactivated > 0 or qty_fixed > 0:
        with open("stock_config_wilbert.json","w") as f:
            json.dump(cfg,f,indent=2,ensure_ascii=False)
    return reactivated + qty_fixed

# Loop
TOKEN = get_token()
H = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID = me["id"]

ITERATIONS = int(os.environ.get("LOOP_ITERATIONS","10"))
SLEEP = int(os.environ.get("LOOP_SLEEP","30"))

total = 0
for i in range(ITERATIONS):
    t0 = time.time()
    print(f"\n=== Iter {i+1}/{ITERATIONS} ===")
    try:
        n = replenish_pass(H, USER_ID)
        total += n
        if n > 0: print(f"  ▶️  {n} cambios")
        else: print(f"  ✓ todo en orden")
    except Exception as e:
        print(f"  err: {e}")
        try:
            TOKEN = get_token()
            H = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
        except: pass

    elapsed = time.time() - t0
    if i < ITERATIONS - 1:
        time.sleep(max(0, SLEEP - elapsed))

print(f"\n✅ Total cambios: {total}")
