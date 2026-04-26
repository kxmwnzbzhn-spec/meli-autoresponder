#!/usr/bin/env python3
"""Safety-net: reactivar TODOS los items pausados de Claribel cada 3 min."""
import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]

# Load config to decrement real_stock when reactivating qty=0
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

count = 0
for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    qty = g.get("available_quantity",0)
    body = {"status":"active"}
    if qty == 0: body["available_quantity"] = 1
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
    if rp.status_code == 200:
        count += 1
        # If we set qty 0→1 and item in cfg, decrement real_stock
        if qty == 0 and iid in cfg:
            real = cfg[iid].get("real_stock",0)
            if real > 0:
                cfg[iid]["real_stock"] = real - 1
        print(f"  ▶️  {iid} qty={qty} → reactivado")
    else:
        print(f"  ❌ {iid} {rp.status_code}: {rp.text[:150]}")

# Save config
if count > 0:
    with open("stock_config_claribel.json","w") as f:
        json.dump(cfg,f,indent=2,ensure_ascii=False)
print(f"\n✅ Total reactivados: {count}")
