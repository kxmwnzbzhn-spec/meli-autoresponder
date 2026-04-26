import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

print(f"Items active: {len(ids)}")
paused = []; errors = []
for iid in ids:
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
    if rp.status_code == 200:
        paused.append(iid)
        print(f"  ⏸️  {iid}")
    else:
        errors.append((iid, rp.status_code, rp.text[:100]))
        print(f"  ❌ {iid}: {rp.status_code}")

# Mark in stock_config to prevent auto-reactivation
try: cfg = json.load(open("stock_config_raymundo.json"))
except: cfg = {}
for iid in paused:
    if iid in cfg:
        cfg[iid]["active"] = False  # disable auto_replenish trigger
        cfg[iid]["paused_by_user"] = True
with open("stock_config_raymundo.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)

print(f"\n✅ Pausados: {len(paused)} | ❌ Errores: {len(errors)}")
print(f"   Marcados en config con paused_by_user=True (no auto-replenish)")
