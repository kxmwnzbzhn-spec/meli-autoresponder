import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]

# Load config
try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}

print(f"=== DIAGNÓSTICO STOCK CLARIBEL ===")
print(f"Total items en config: {len(cfg)}")
print()

# Check ALL items: pausados, con qty=0, no en config
issues = []

# 1) Buscar items pausados
print("--- Items PAUSADOS ahora mismo ---")
ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    in_cfg = iid in cfg
    real = cfg.get(iid,{}).get("real_stock","NO_EN_CFG") if in_cfg else "NO_EN_CFG"
    title = g.get("title","")[:55]
    print(f"  ⏸️  {iid} | qty={g.get('available_quantity')} sold={g.get('sold_quantity')} | real={real} | '{title}'")
    issues.append((iid, "PAUSED", g.get('available_quantity'), real, title))

# 2) Buscar items active con qty=0 (raro pero posible)
print(f"\n--- Items ACTIVE pero con qty=0 ---")
ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

print(f"Total active: {len(ids)}")
for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,available_quantity,title",headers=H,timeout=10).json()
    qty = g.get("available_quantity",0)
    if qty == 0:
        in_cfg = iid in cfg
        real = cfg.get(iid,{}).get("real_stock","NO_EN_CFG") if in_cfg else "NO_EN_CFG"
        title = g.get("title","")[:55]
        print(f"  ⚠️  {iid} qty=0 active | real={real} | '{title}'")
        issues.append((iid, "ACTIVE_QTY_0", 0, real, title))

print(f"\n=== TOTAL ISSUES: {len(issues)} ===")
