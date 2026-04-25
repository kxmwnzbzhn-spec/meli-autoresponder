import os, requests, json, time
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Find ALL items (active + paused)
all_ids = set()
for st in ["active","paused"]:
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}", headers=H).json()
        b = rr.get("results",[])
        if not b: break
        all_ids.update(b)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

# Load existing config
try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}

added = []
reactivated = []
print(f"Total items: {len(all_ids)}\n")

for iid in all_ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = (g.get("title","") or "")[:55]
    status = g.get("status","")
    qty = g.get("available_quantity",0)
    sold = g.get("sold_quantity",0)
    has_vars = bool(g.get("variations"))
    cat = g.get("category_id","")
    
    print(f"  {iid} [{status}] qty={qty} sold={sold} vars={has_vars} cat={cat[:8]} '{title[:45]}'")
    
    # If paused with qty=0, reactivate with qty=1
    if status == "paused" and qty == 0 and not has_vars:
        rr = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                         json={"available_quantity":1, "status":"active"})
        if rr.status_code == 200:
            print(f"    ✅ REACTIVATED qty→1")
            reactivated.append(iid)
        else:
            print(f"    ❌ reactivate failed {rr.status_code}: {rr.text[:200]}")
        time.sleep(0.5)
    
    # Add to config if not present and is single-SKU (no variations)
    if iid not in cfg and not has_vars and status in ("active","paused"):
        cfg[iid] = {
            "line": "Auto-added-perfume" if cat == "MLM1271" else "Auto-added",
            "label": title[:40],
            "price": g.get("price"),
            "catalog_product_id": g.get("catalog_product_id"),
            "auto_replenish": True,
            "min_visible": 1,
            "real_stock": 10,
            "daily_reset_to": 10,
            "active": True,
            "condition": g.get("condition","new"),
            "type": "catalog_no_variations"
        }
        added.append(iid)
        print(f"    ➕ AÑADIDO al config (real_stock=10)")
    time.sleep(0.3)

with open("stock_config_claribel.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n✅ RESUMEN:")
print(f"  Reactivados: {len(reactivated)}")
for iid in reactivated: print(f"    {iid}")
print(f"  Añadidos al bot: {len(added)}")
for iid in added: print(f"    {iid} → {cfg[iid]['label']}")
print(f"  Total items en config: {len(cfg)}")
