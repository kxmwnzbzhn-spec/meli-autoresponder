#!/usr/bin/env python3
"""Reactivar TODOS los items de Raymundo + habilitar auto_replenish + setup como winner."""
import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Get ALL items (paused + active)
all_ids = set()
for st in ("active","paused"):
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        all_ids.update(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
print(f"Total items Raymundo: {len(all_ids)}")

try: cfg = json.load(open("stock_config_raymundo.json"))
except: cfg = {}

reactivated = 0; cfg_fixed = 0
for iid in all_ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    title = g.get("title","")[:50]
    qty = g.get("available_quantity",0)
    status = g.get("status","")
    is_catalog = g.get("catalog_listing", False)
    
    # Reactivate if paused
    if status == "paused":
        body = {"status":"active"}
        if qty == 0: body["available_quantity"] = 1
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
        if rp.status_code == 200:
            reactivated += 1
            print(f"  ▶️  REACTIVADO {iid} | qty={qty} | '{title}'")
    
    # Update/add to config
    if iid in cfg:
        cfg[iid]["active"] = True
        cfg[iid]["auto_replenish"] = True
        if "paused_by_user" in cfg[iid]:
            del cfg[iid]["paused_by_user"]
        cfg_fixed += 1
    else:
        # Add new
        if is_catalog:
            cfg[iid] = {
                "line": "Catalog-Raymundo-Winner",
                "label": title[:45],
                "price": g.get("price",499),
                "catalog_product_id": g.get("catalog_product_id"),
                "auto_replenish": True,
                "min_visible": 1,
                "real_stock": 15,
                "daily_reset_to": 15,
                "active": True,
                "condition": "new",
                "type": "catalog_no_variations"
            }
            cfg_fixed += 1
            print(f"  ➕ AÑADIDO {iid} a config")

with open("stock_config_raymundo.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
print(f"\n✅ Reactivados: {reactivated} | Config fixed: {cfg_fixed}")
