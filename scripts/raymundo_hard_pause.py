"""
RAYMUNDO HARD PAUSE
===================
Pausa TODOS los items y deshabilita auto_replenish en config.
Verifica que sigan pausados después.
"""
import os, requests, json, time
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Get ALL items (active + paused)
all_ids = set()
for st in ("active","paused"):
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        all_ids.update(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

print(f"Total items: {len(all_ids)}\n")

# Multi-get current status
batch = list(all_ids); items_data = {}
for i in range(0, len(batch), 20):
    chunk = ",".join(batch[i:i+20])
    rr = requests.get(f"https://api.mercadolibre.com/items?ids={chunk}&attributes=id,title,status,available_quantity",headers=H,timeout=20).json()
    for it in rr:
        if it.get("code") == 200:
            items_data[it["body"]["id"]] = it["body"]

paused_now = []; already_paused = []; errors = []
for iid, b in items_data.items():
    title = (b.get("title") or "")[:50]
    status = b.get("status")
    if status == "paused":
        already_paused.append(iid)
        print(f"  ✓ ya pausado {iid} | {title}")
        continue
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
    if rp.status_code == 200:
        paused_now.append(iid)
        print(f"  ⏸️  PAUSADO {iid} | {title}")
    else:
        errors.append((iid, rp.status_code, rp.text[:120]))
        print(f"  ❌ {iid}: {rp.status_code} {rp.text[:100]}")
    time.sleep(0.15)

# HARD config update: disable auto_replenish AND mark paused_by_user=True for ALL items
try: cfg = json.load(open("stock_config_raymundo.json"))
except FileNotFoundError: cfg = {}

for iid in items_data.keys():
    if iid not in cfg:
        cfg[iid] = {"line":"Raymundo","label":(items_data[iid].get("title") or "")[:45]}
    cfg[iid]["active"] = False
    cfg[iid]["auto_replenish"] = False  # CRÍTICO
    cfg[iid]["paused_by_user"] = True
    cfg[iid]["hard_pause"] = True

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n=== RESUMEN ===")
print(f"⏸️  Pausados ahora:    {len(paused_now)}")
print(f"✓  Ya estaban pausados: {len(already_paused)}")
print(f"❌ Errores: {len(errors)}")

# Re-verify after 5s
time.sleep(5)
print("\n=== VERIFICACIÓN POST-PAUSE ===")
still_active = []
for i in range(0, len(batch), 20):
    chunk = ",".join(batch[i:i+20])
    rr = requests.get(f"https://api.mercadolibre.com/items?ids={chunk}&attributes=id,status",headers=H,timeout=20).json()
    for it in rr:
        if it.get("code") == 200 and it["body"].get("status") == "active":
            still_active.append(it["body"]["id"])

if still_active:
    print(f"⚠️  ATENCIÓN: {len(still_active)} items siguen ACTIVOS:")
    for iid in still_active: print(f"    {iid}")
else:
    print(f"✅ Todos pausados correctamente ({len(items_data)} items)")
