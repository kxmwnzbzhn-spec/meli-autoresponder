import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}

# Get all 22 active items + sus precios actuales como "original" para calcular floor 70%
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
sid = me["id"]
ids = []
s = 0
while True:
    d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}", headers=H, timeout=15).json()
    got = d.get("results", []) or []
    if not got: break
    ids.extend(got)
    s += 100
    if s >= d.get("paging",{}).get("total",0): break

# Cargar state existente
state_path = "catalog_war_state.json"
state = {"items": {}}
try:
    with open(state_path) as f: state = json.load(f)
except: pass

# Para cada item, asegurar que tiene original_price (usamos precio actual como base)
fixed = 0
for iid in ids:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    cur = float(item.get("price", 0))
    if iid not in state["items"]:
        state["items"][iid] = {}
    cur_orig = state["items"][iid].get("original_price")
    if not cur_orig or cur_orig < cur * 0.5:  # si está vacío o muy bajo, usar el actual
        state["items"][iid]["original_price"] = cur * 1.4  # 40% más alto = ceiling, 70% como floor
        state["items"][iid]["last_known_price"] = cur
        fixed += 1
        print(f"  + {iid}: original_price seteado a ${cur*1.4:.0f} (floor=${cur*0.98:.0f})")

with open(state_path, "w") as f:
    json.dump(state, f, indent=2)
print(f"\n✅ {fixed}/{len(ids)} items con state.json actualizado")
