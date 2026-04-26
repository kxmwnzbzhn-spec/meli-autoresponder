#!/usr/bin/env python3
"""Safety-net: reactivar items pausados Claribel. Loop 10×30s = check cada 30s durante 5 min."""
import os, time, requests, json

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    return r["access_token"]

def reactivate_pass(H, USER_ID):
    """Una pasada: reactivar todos los pausados."""
    try: cfg = json.load(open("stock_config_claribel.json"))
    except: cfg = {}
    
    ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    if not ids: return 0
    count = 0
    for iid in ids:
        g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
        qty = g.get("available_quantity",0)
        body = {"status":"active"}
        if qty == 0: body["available_quantity"] = 1
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
        if rp.status_code == 200:
            count += 1
            if qty == 0 and iid in cfg:
                real = cfg[iid].get("real_stock",0)
                if real > 0:
                    cfg[iid]["real_stock"] = real - 1
            print(f"  ▶️  {iid} qty={qty} → activo (real_stock-=1 si aplica)")
        else:
            print(f"  ❌ {iid} {rp.status_code}: {rp.text[:120]}")
    
    if count > 0:
        with open("stock_config_claribel.json","w") as f:
            json.dump(cfg,f,indent=2,ensure_ascii=False)
    return count

# Loop 10 iteraciones × 30s = 5 min de cobertura continua
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
        n = reactivate_pass(H, USER_ID)
        total += n
        if n > 0: print(f"  ▶️  {n} reactivados")
        else: print(f"  ✓ 0 pausados")
    except Exception as e:
        print(f"  err: {e}")
        # Refresh token if needed
        try:
            TOKEN = get_token()
            H = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
        except: pass
    
    elapsed = time.time() - t0
    if i < ITERATIONS - 1:
        sleep_remain = max(0, SLEEP - elapsed)
        time.sleep(sleep_remain)

print(f"\n✅ Total reactivados en este run: {total}")
