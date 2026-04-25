import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_CLARIBEL","")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Check Go 4 unified items
ITEMS = ["MLM5239571436", "MLM5244862560"]
for iid in ITEMS:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    if g.get("status") == "not_found" or "error" in g:
        print(f"  {iid} → not found/error")
        continue
    print(f"\n{iid}: {g.get('title','?')[:55]}")
    print(f"  status={g.get('status')} cond={g.get('condition')} price=${g.get('price')}")
    print(f"  available_quantity total: {g.get('available_quantity')}")
    for v in g.get("variations",[]):
        color = "?"
        for ac in v.get("attribute_combinations",[]):
            if ac.get("id")=="COLOR":
                color = ac.get("value_name","?")
        print(f"    var [{color}] visible={v.get('available_quantity',0)} | sold={v.get('sold_quantity',0)}")

# Check stock config
print("\n=== stock_config_claribel.json ===")
try:
    with open("stock_config_claribel.json") as f:
        cfg = json.load(f)
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"err: {e}")

# Check if claribel listed in main stock_config.json
print("\n=== main stock_config.json: Claribel items ===")
try:
    with open("stock_config.json") as f:
        cfg = json.load(f)
    for iid, v in cfg.items():
        if isinstance(v, dict) and (v.get("account") == "claribel" or "claribel" in str(v).lower()):
            print(f"  {iid}: {v.get('label','')} stock={v.get('real_stock')}")
except: pass
