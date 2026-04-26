"""Raymundo perpetual replenish — loop 10×30s cada 5 min con auto-trigger chain."""
import os, time, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    return r["access_token"]

def reactivate_pass(H, USER_ID):
    try: cfg = json.load(open("stock_config_raymundo.json"))
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
        # Skip items marked paused_by_user
        if iid in cfg and cfg[iid].get("paused_by_user"):
            continue
        g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
        qty = g.get("available_quantity",0)
        body = {"status":"active"}
        if qty == 0: body["available_quantity"] = 1
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
        if rp.status_code == 200:
            count += 1
            if qty == 0 and iid in cfg:
                real = cfg[iid].get("real_stock",0)
                if real > 0: cfg[iid]["real_stock"] = real - 1
            print(f"  ▶️ {iid} qty={qty} → activo")
    if count > 0:
        with open("stock_config_raymundo.json","w") as f:
            json.dump(cfg,f,indent=2,ensure_ascii=False)
    return count

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
    except Exception as e:
        print(f"err: {e}")
        try: TOKEN = get_token(); H["Authorization"] = f"Bearer {TOKEN}"
        except: pass
    elapsed = time.time() - t0
    if i < ITERATIONS-1: time.sleep(max(0,SLEEP-elapsed))
print(f"\n✅ Total reactivados: {total}")
