import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Items paused
print("=== Items PAUSADOS Juan ===")
ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
print(f"Total paused: {len(ids)}")

# Load main bot's stock_config (Juan items)
try: cfg = json.load(open("stock_config.json"))
except: cfg = {}

for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    qty = g.get("available_quantity",0)
    sold = g.get("sold_quantity",0)
    title = g.get("title","")[:50]
    in_cfg = iid in cfg
    cfg_real = cfg.get(iid,{}).get("real_stock","NO_EN_CFG") if in_cfg else "NO_EN_CFG"
    cfg_active = cfg.get(iid,{}).get("active",None) if in_cfg else None
    cfg_replenish = cfg.get(iid,{}).get("auto_replenish",None) if in_cfg else None
    print(f"  ⏸️  {iid} qty={qty} sold={sold} | cfg={in_cfg} active={cfg_active} replenish={cfg_replenish} real={cfg_real}")
    print(f"      '{title}'")

# Active with qty=0
print(f"\n=== Items ACTIVE con qty=0 ===")
ids2 = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids2.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
print(f"Total active: {len(ids2)}")
for iid in ids2:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,available_quantity",headers=H,timeout=10).json()
    if g.get("available_quantity",0) == 0:
        in_cfg = iid in cfg
        real = cfg.get(iid,{}).get("real_stock","NO_EN_CFG") if in_cfg else "NO_EN_CFG"
        print(f"  ⚠️  {iid} qty=0 active | cfg={in_cfg} real={real} | '{g.get('title','')[:50]}'")
