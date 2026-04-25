import os, requests, json, time
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
TOKEN = r["access_token"]
H = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}

for iid, info in cfg.items():
    if not info.get("active"): continue
    if not info.get("auto_replenish", True): continue
    
    cur = requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all", headers=H).json()
    if cur.get("status") not in ("active","paused"): continue
    
    title = (cur.get("title","") or "")[:50]
    print(f"\n  {iid}: '{title}'")
    
    # Type 1: variations item (Go 4 unificada)
    if cur.get("variations") and info.get("variations"):
        new_vars = []
        any_repuesto = False
        for v in cur.get("variations") or []:
            color = None
            for ac in v.get("attribute_combinations",[]):
                if ac.get("id")=="COLOR": color=ac.get("value_name"); break
            curr = v.get("available_quantity",0)
            real_stock = info.get("variations",{}).get(color,0)
            print(f"    {color} visible={curr} real={real_stock}")
            
            if curr==0 and real_stock>0:
                nv = {
                    "id":v.get("id"),"price":v.get("price"),"available_quantity":1,
                    "attribute_combinations":v.get("attribute_combinations",[]),
                    "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
                }
                new_vars.append(nv)
                info["variations"][color] = real_stock-1
                any_repuesto = True
                print(f"      -> REPUESTO visible=1, real={real_stock-1}")
            else:
                nv = {
                    "id":v.get("id"),"price":v.get("price"),"available_quantity":curr,
                    "attribute_combinations":v.get("attribute_combinations",[]),
                    "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
                }
                new_vars.append(nv)
        if any_repuesto:
            rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"variations":new_vars}, timeout=30)
            print(f"    update: {rp.status_code}")
    
    # Type 2: catalog single SKU (no variations)
    elif info.get("type") == "catalog_no_variations":
        curr = cur.get("available_quantity",0)
        real_stock = info.get("real_stock",0)
        print(f"    [single] visible={curr} real={real_stock}")
        if curr==0 and real_stock>0:
            rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                             json={"available_quantity":1}, timeout=30)
            if rp.status_code == 200:
                info["real_stock"] = real_stock-1
                print(f"      -> REPUESTO visible=1, real={real_stock-1}")
            else:
                print(f"      ❌ replenish failed {rp.status_code}: {rp.text[:200]}")

json.dump(cfg, open("stock_config_claribel.json","w"), indent=2, ensure_ascii=False)
print("\nDone")
