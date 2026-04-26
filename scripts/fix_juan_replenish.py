"""Fix: enable auto_replenish=True para todos los items catalog_listing de Juan + reactivar pausados ahora."""
import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]

try: cfg = json.load(open("stock_config.json"))
except: cfg = {}

# 1) Get ALL Juan items (active + paused)
all_ids = set()
for st in ("active","paused"):
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        all_ids.update(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
print(f"Total items active+paused: {len(all_ids)}")

fixed = 0; reactivated = 0
for iid in all_ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H,timeout=10).json()
    if not g.get("catalog_listing"): continue  # solo catalog_listing
    
    title = g.get("title","")[:55]
    qty = g.get("available_quantity",0)
    status = g.get("status","")
    
    # Enable auto_replenish in config
    if iid in cfg:
        old_replenish = cfg[iid].get("auto_replenish")
        cfg[iid]["auto_replenish"] = True
        cfg[iid]["active"] = True
        if old_replenish != True:
            fixed += 1
            print(f"  ✅ {iid} cfg: auto_replenish=True | '{title}'")
    else:
        # Add to config with default settings
        cfg[iid] = {
            "real_stock": 15,
            "auto_replenish": True,
            "min_visible_stock": 1,
            "replenish_quantity": 1,
            "label": title[:45],
            "account": "juan",
            "type": "catalog_no_variations"
        }
        fixed += 1
        print(f"  ➕ {iid} ADDED to cfg | '{title}'")
    
    # Reactivate if paused with stock available
    if status == "paused":
        body = {"status":"active"}
        if qty == 0: body["available_quantity"] = 1
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
        if rp.status_code == 200:
            reactivated += 1
            print(f"     ▶️  REACTIVADO {iid}")

with open("stock_config.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
print(f"\n✅ Fixed {fixed} items en cfg | Reactivados {reactivated}")
