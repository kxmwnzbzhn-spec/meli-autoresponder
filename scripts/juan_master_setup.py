"""
1) Para los 14 items de Juan: set available_quantity=1 en MELI
2) Crear stock_config_juan.json con master stock total = lo que tenia + extras solicitados:
   - Charge 6 (3 items): master = current_avail + 15 cada uno
   - Flip 7 (3 items): master = current_avail + 20 cada uno
   - Resto: master = current_avail (lo que tenían)
3) auto_replenish=true min_visible=1 para todos
"""
import os, requests, json, time
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
sid = me["id"]

ids = []
s = 0
while True:
    d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}", headers=H).json()
    got = d.get("results", []) or []
    if not got: break
    ids.extend(got); s += 100
    if s >= d.get("paging",{}).get("total",0): break

# Cargar config existente
config_path = "stock_config_juan.json"
config = {}
try:
    with open(config_path) as f: config = json.load(f)
except: pass

# Aplicar visibilidad y master stock
ALREADY_OK = 0; UPDATED = 0; ERR = 0
for iid in ids:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = item.get("title","")
    cur_avail = int(item.get("available_quantity", 0))
    title_lc = title.lower()

    # Determinar master stock
    extra = 0
    line = "default"
    if "charge 6" in title_lc and "reacond" in title_lc:
        extra = 15; line = "Juan-Charge6-Reacond"
    elif "flip 7" in title_lc and "reacond" in title_lc:
        extra = 20; line = "Juan-Flip7-Reacond"
    elif "go 4" in title_lc:
        line = "Juan-Go4"
    elif "sony" in title_lc:
        line = "Juan-Sony"
    elif "grip" in title_lc:
        line = "Juan-Grip"

    # Master = lo que tenia (cur_avail) + extra. Si cur_avail era 1, master = 1 + extra
    master_total = cur_avail + extra

    # Update config
    cfg = config.get(iid, {})
    cfg.update({
        "auto_replenish": True,
        "min_visible": 1,
        "master_stock": master_total,
        "line": line,
        "title": title[:80],
        "active": True,
    })
    config[iid] = cfg

    # Set visible=1 en MELI si está arriba
    if cur_avail > 1:
        try:
            r = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"available_quantity":1}, timeout=15)
            if r.status_code in (200,201):
                print(f"  ✓ {iid} avail {cur_avail}→1 + master={master_total} ({line})")
                UPDATED += 1
            else:
                print(f"  ✗ {iid}: HTTP {r.status_code} {r.text[:120]}")
                ERR += 1
        except Exception as e:
            print(f"  ✗ {iid}: {e}"); ERR += 1
    else:
        if extra > 0:
            print(f"  ⊕ {iid} ya en avail=1, master {cur_avail}→{master_total} (+{extra}, {line})")
        else:
            print(f"  ✓ {iid} ya en avail=1, master={master_total} ({line})")
        ALREADY_OK += 1
    time.sleep(0.3)

# Guardar config
with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n=== TOTAL: {UPDATED} actualizados a 1 visible | {ALREADY_OK} ya OK | {ERR} errores ===")
print(f"=== {len(config)} items en stock_config_juan.json ===")

# Telegram
tg_t = os.environ.get("TELEGRAM_BOT_TOKEN"); tg_c = os.environ.get("TELEGRAM_CHAT_ID")
if tg_t and tg_c:
    msg = f"📦 Juan setup:\n• {UPDATED} items reducidos a 1 visible\n• {ALREADY_OK} ya OK\n• Charge 6 +15 master/color\n• Flip 7 +20 master/color\n• Auto-replenish activado en 14 items"
    requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage", data={"chat_id":tg_c, "text":msg}, timeout=10)
