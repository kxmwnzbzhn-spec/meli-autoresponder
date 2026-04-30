#!/usr/bin/env python3
"""Wilbert: replenish con STOCK COMPARTIDO por línea.

stock_lines_wilbert.json mantiene stock real por línea (ej: Mandarin-Sky-shared: 11).
Multiple items pueden apuntar a la misma línea — el stock se decrementa de la línea, no del item.

Loop: cada 30s checa si hay items pausados o con qty<1, los repone si la línea tiene stock.
"""
import os, time, requests, json

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_WILBERT"]

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    return r["access_token"]

def load_lines():
    try:
        with open("stock_lines_wilbert.json") as f:
            d = json.load(f)
            return d.get("lines", {}), d
    except:
        return {}, {"lines":{}}

def save_lines(full):
    with open("stock_lines_wilbert.json","w") as f:
        json.dump(full,f,indent=2,ensure_ascii=False)

def replenish_pass(H, USER_ID):
    try: cfg = json.load(open("stock_config_wilbert.json"))
    except: cfg = {}
    lines, lines_full = load_lines()

    # 1. Listar pausados
    paused_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        paused_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

    changes = 0
    # 2. Reactivar pausados con stock disponible en su línea
    for iid in paused_ids:
        if iid not in cfg: continue
        ic = cfg[iid]
        if not ic.get("auto_replenish", False) or not ic.get("active", True): continue
        line = ic.get("line", "")
        line_stock = lines.get(line, 0)
        if line_stock <= 0:
            print(f"  ⏸️  {iid} línea '{line}' sin stock ({line_stock}) → no reactivar")
            continue

        body = {"status":"active","available_quantity":1}
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
        if rp.status_code == 200:
            lines[line] = line_stock - 1
            print(f"  ▶️  {iid} reactivado | línea '{line}': {line_stock}→{line_stock-1}")
            changes += 1
        else:
            print(f"  ❌ {iid} {rp.status_code}: {rp.text[:120]}")

    # 3. Listar activos con qty=0 → subirlos a 1 si línea tiene stock
    active_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        active_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

    for iid in active_ids:
        if iid not in cfg: continue
        ic = cfg[iid]
        if not ic.get("auto_replenish",False): continue
        gg = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=available_quantity,status",headers=H,timeout=10).json()
        qty = gg.get("available_quantity",0)
        if qty < 1 and gg.get("status")=="active":
            line = ic.get("line","")
            line_stock = lines.get(line, 0)
            if line_stock > 0:
                rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":1},timeout=15)
                if rp.status_code == 200:
                    lines[line] = line_stock - 1
                    print(f"  🔢 {iid} qty 0→1 | línea '{line}': {line_stock}→{line_stock-1}")
                    changes += 1

    if changes > 0:
        lines_full["lines"] = lines
        save_lines(lines_full)
    return changes, lines

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
        n, lines = replenish_pass(H, USER_ID)
        total += n
        if n > 0: print(f"  ▶️  {n} cambios | líneas restantes: {sum(lines.values())}")
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
