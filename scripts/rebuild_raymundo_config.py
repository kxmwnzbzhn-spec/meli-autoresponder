"""Reconstruye stock_config_raymundo.json desde TODOS los items vivos en MELI.
Detecta modelo (Clip 5/Go 4/Go 3) y color del título.
Asigna stock pool correcto y catalog_war=True a todos los catálogos.
"""
import os, requests, json, time, re

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

POOL_SIZE = {
    ("Clip 5", "Morado"):      256,
    ("Clip 5", "Rojo"):        164,
    ("Clip 5", "Negro"):       246,
    ("Clip 5", "Azul"):        480,
    ("Clip 5", "Camuflaje"):   240,
    ("Clip 5", "Rosa"):        204,
    ("Clip 5", "Mixto"):        40,
    ("Go 4", "Negro"):         130,
    ("Go 4", "Azul"):          480,
    ("Go 4", "Rojo"):          407,
    ("Go 4", "Aqua"):         1013,
    ("Go 4", "Azul Marino"):   466,
    ("Go 4", "Camuflaje"):     549,
    ("Go 4", "Rosa"):          129,
    ("Go 3", "Negro"):         936,
}

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me['id']
print(f"Cuenta: {me['nickname']} ({uid})\n")

# Cargar config actual (preservar items custom como Charge/Flip etc)
try:
    with open("stock_config_raymundo.json") as f:
        cfg = json.load(f)
except Exception:
    cfg = {}
print(f"Config existente: {len(cfg)} items")

# Listar TODOS los items active de Raymundo
print("\nFetching ALL active items...")
all_iids = []
offset = 0
while True:
    r = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search",
                     headers=H, params={"status":"active","limit":100,"offset":offset},
                     timeout=20).json()
    results = r.get("results",[])
    all_iids.extend(results)
    total = r.get("paging",{}).get("total", 0)
    offset += len(results)
    if not results or offset >= total or offset >= 2000: break
print(f"Items activos: {len(all_iids)}")

def detect(title):
    t = title.lower().replace("bluetooth"," ")
    # Modelo
    if "clip 5" in t or "clip5" in t: model = "Clip 5"
    elif "go 4" in t or "go4" in t:   model = "Go 4"
    elif "go 3" in t or "go3" in t:   model = "Go 3"
    else: return None, None
    # Color
    if any(x in t for x in ["camuflaj","camo","camuflad"]): color = "Camuflaje"
    elif "azul marino" in t or "azul acero" in t: color = "Azul Marino"
    elif any(x in t for x in ["aqua","celeste"]): color = "Aqua"
    elif "negr" in t or "black" in t: color = "Negro"
    elif "roj" in t or " red" in t: color = "Rojo"
    elif "rosa" in t or "pink" in t: color = "Rosa"
    elif any(x in t for x in ["morado","violeta","purple","violet","purpura","púrpura"]): color = "Morado"
    elif " azul" in (" "+t) or " blue" in (" "+t): color = "Azul"
    else: color = None
    return model, color

# Procesar todos
batch_get_chunks = [all_iids[i:i+20] for i in range(0,len(all_iids),20)]
items_data = []
for chunk in batch_get_chunks:
    ids_str = ",".join(chunk)
    r = requests.get("https://api.mercadolibre.com/items",
                     headers=H, params={"ids":ids_str,
                       "attributes":"id,title,price,catalog_listing,catalog_product_id,available_quantity,status"},
                     timeout=20).json()
    for itm in r:
        if itm.get("code") == 200:
            items_data.append(itm.get("body"))
    time.sleep(0.3)

print(f"Items con data: {len(items_data)}")

# Build new entries for catálogo items
added = 0
updated = 0
pubs_by_pool = {}
for it in items_data:
    iid = it.get("id")
    if not it.get("catalog_listing"): continue  # solo catálogo
    title = it.get("title","")
    model, color = detect(title)
    if not model or not color or (model, color) not in POOL_SIZE:
        continue
    # Floor por modelo
    floor = 199 if model == "Go 4" else (99 if model == "Go 3" else 599)
    cpid = it.get("catalog_product_id")
    if iid not in cfg:
        cfg[iid] = {
            "label": f"{model} {color}",
            "real_stock": 0,  # se asigna abajo
            "min_visible": 1,
            "auto_replenish": True,
            "replenish_quantity": 1,
            "catalog_war": True,
            "floor_price": floor,
            "ceiling_price": 1499,
            "color": color,
            "model": model,
            "catalog_product_id": cpid,
        }
        added += 1
    else:
        cfg[iid]["catalog_war"] = True
        cfg[iid]["floor_price"] = floor
        cfg[iid]["model"] = model
        cfg[iid]["color"] = color
        if cpid: cfg[iid]["catalog_product_id"] = cpid
        if not cfg[iid].get("auto_replenish"): cfg[iid]["auto_replenish"] = True
        if not cfg[iid].get("min_visible"): cfg[iid]["min_visible"] = 1
        updated += 1
    pubs_by_pool.setdefault((model, color), []).append(iid)

# Reparto stock por pool
print(f"\n+{added} nuevos, {updated} actualizados")
print("\nReparto pool:")
for key, total in POOL_SIZE.items():
    pubs = pubs_by_pool.get(key, [])
    if not pubs: continue
    n = len(pubs)
    per = total // n
    rem = total - per * n
    for i, iid in enumerate(pubs):
        amt = per + (rem if i == 0 else 0)
        cfg[iid]["real_stock"] = max(0, amt - 1)
        cfg[iid]["pool_total"] = total
    print(f"  {key[0]} {key[1]}: {total}u / {n} pubs = {per}u c/u")

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

# Stats final
catalog_war_count = sum(1 for v in cfg.values() if v.get("catalog_war"))
print(f"\n✅ stock_config_raymundo.json: {len(cfg)} items totales, {catalog_war_count} con catalog_war")

if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown",
        "text": (
            f"🔧 *Stock config Raymundo reconstruido*\n\n"
            f"Items totales: {len(cfg)}\n"
            f"Con catalog_war: *{catalog_war_count}*\n"
            f"+{added} nuevos / {updated} actualizados\n\n"
            f"Disparando catalog war en próximo cron (5 min)..."
        )}, timeout=20)
