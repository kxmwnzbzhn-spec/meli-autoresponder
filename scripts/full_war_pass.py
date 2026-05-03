#!/usr/bin/env python3
"""ALL-IN-ONE: rebuild config + deep audit + force-fix losing en UN solo run.

Pasos:
1. Lista TODOS los items active de Raymundo desde MELI
2. Para cada catalog_listing: detecta model/color del titulo
3. Setea floor/ceiling según modelo:
   - Go 4:    floor 449,  ceiling 1499
   - Go 3:    floor 349,  ceiling 599  + FORCE precio = 499
   - Clip 5:  floor 699,  ceiling 899
4. Consulta ptw para cada uno
5. Si losing/sharing: bajar a ptw-1 (respetando floor)
6. Si winning con precio mayor a ptw-1: cap a ptw-1
7. Reportar floor blocks
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

FLOORS   = {"Go 4": 449, "Go 3": 399, "Clip 5": 699}
CEILINGS = {"Go 4": 699,  "Go 3": 599, "Clip 5": 899}
GO3_FORCE_PRICE = 499
GO4_CEILING = 699  # explicito: any Go 4 > $699 se baja a $699

POOL_SIZE = {
    ("Clip 5","Morado"):256,("Clip 5","Rojo"):164,("Clip 5","Negro"):246,
    ("Clip 5","Azul"):480,("Clip 5","Camuflaje"):240,("Clip 5","Rosa"):204,
    ("Clip 5","Mixto"):40,
    ("Go 4","Negro"):130,("Go 4","Azul"):480,("Go 4","Rojo"):407,
    ("Go 4","Aqua"):1013,("Go 4","Azul Marino"):466,("Go 4","Camuflaje"):549,
    ("Go 4","Rosa"):129,
    ("Go 3","Negro"):936,
}

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me['id']
print(f"Cuenta: {me['nickname']} ({uid})\n")

# Carga config
try:
    with open("stock_config_raymundo.json") as f:
        cfg = json.load(f)
except Exception:
    cfg = {}


# === BORRAR items que no nos corresponden ===
DELETE_IIDS = ["MLM2904767887", "MLM2904680457"]
for d_iid in DELETE_IIDS:
    pr = requests.put(f"https://api.mercadolibre.com/items/{d_iid}",
                      headers=H, json={"status": "closed"})
    print(f"  ⛔ CLOSED {d_iid} → {pr.status_code}")
    cfg.pop(d_iid, None)


# Listar TODOS los items active
print("Fetching active items...")
all_iids = []
offset = 0
while True:
    r = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search",
                     headers=H, params={"status":"active","limit":100,"offset":offset},
                     timeout=20).json()
    results = r.get("results",[])
    all_iids.extend(results)
    total = r.get("paging",{}).get("total",0)
    offset += len(results)
    if not results or offset >= total or offset >= 2000: break
print(f"Active items: {len(all_iids)}\n")

def detect(title):
    t = (title or "").lower().replace("bluetooth"," ")
    if "clip 5" in t or "clip5" in t: model = "Clip 5"
    elif "go 4" in t or "go4" in t:   model = "Go 4"
    elif "go 3" in t or "go3" in t:   model = "Go 3"
    else: return None, None
    if any(x in t for x in ["camuflaj","camo","camuflad"]): color = "Camuflaje"
    elif "azul marino" in t or "azul acero" in t: color = "Azul Marino"
    elif any(x in t for x in ["aqua","celeste"]): color = "Aqua"
    elif "negr" in t or "black" in t: color = "Negro"
    elif "roj" in t or " red" in t: color = "Rojo"
    elif "rosa" in t or "pink" in t: color = "Rosa"
    elif any(x in t for x in ["morado","violeta","purple","violet","purpura","púrpura"]): color = "Morado"
    elif " azul" in (" "+t) or " blue" in (" "+t): color = "Azul"
    else: color = "?"
    return model, color

# Get all items in chunks
items_data = []
for i in range(0, len(all_iids), 20):
    chunk = all_iids[i:i+20]
    r = requests.get("https://api.mercadolibre.com/items",
                     headers=H, params={"ids":",".join(chunk),
                       "attributes":"id,title,price,catalog_listing,catalog_product_id,available_quantity,status"},
                     timeout=20).json()
    for resp in r:
        if resp.get("code") == 200:
            items_data.append(resp.get("body"))
    time.sleep(0.2)

# Build/update config + classify
catalog_items = []
for it in items_data:
    if not it.get("catalog_listing") or it.get("status") != "active":
        continue
    iid = it["id"]
    title = it.get("title","")
    cur = it.get("price")
    cpid = it.get("catalog_product_id")
    model, color = detect(title)
    if not model: continue

    floor = FLOORS.get(model, 199)
    ceiling = CEILINGS.get(model, 1499)

    if iid not in cfg:
        cfg[iid] = {
            "label": f"{model} {color or '?'}",
            "real_stock": 50, "min_visible": 1,
            "auto_replenish": True, "replenish_quantity": 1,
        }
    cfg[iid].update({
        "model": model, "color": color or cfg[iid].get("color"),
        "label": cfg[iid].get("label") or f"{model} {color}",
        "floor_price": floor, "ceiling_price": ceiling,
        "catalog_war": True, "catalog_product_id": cpid,
    })
    catalog_items.append((iid, model, color, cur, floor, ceiling))

print(f"Catalog items con war activo: {len(catalog_items)}\n")

# === FASE 2: ACCIÓN POR ITEM ===
stats = {"go3_force":0, "winning_cap":0, "fixed":0, "floor_block":0,
         "not_listed":0, "errors":0, "untouched":0}
fixed_list = []
floor_blocks = []

for iid, model, color, cur, floor, ceiling in catalog_items:
    try:
        # Go 3 → forzar a $499
        if model == "Go 3":
            if cur != GO3_FORCE_PRICE:
                pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                  headers=H, json={"price": GO3_FORCE_PRICE})
                if pr.status_code == 200:
                    stats["go3_force"] += 1
                    print(f"  📌 GO3 ${cur}→$499 {iid}")
            time.sleep(0.15); continue

        # PTW lookup
        ptw_resp = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=8).json()
        st = ptw_resp.get("status")
        ptw = ptw_resp.get("price_to_win")

        if st == "winning":
            if ptw is not None:
                target = max(floor, round(ptw - 1, 0))
                if target < cur:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        stats["winning_cap"] += 1
                        print(f"  🛡️ CAP {iid}: ${cur}→${target}")
                else:
                    stats["untouched"] += 1
            else:
                stats["untouched"] += 1
        elif st in ("losing","sharing","competing"):
            if ptw is not None:
                target = max(floor, round(ptw - 1, 0))
                if target < cur and target >= floor:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        stats["fixed"] += 1
                        fixed_list.append({"iid":iid,"old":cur,"new":target,"st":st})
                        print(f"  ✅ FIX {st} {iid}: ${cur}→${target} (ptw=${ptw})")
                elif ptw < floor:
                    stats["floor_block"] += 1
                    floor_blocks.append({"iid":iid,"model":model,"color":color,
                                          "cur":cur,"ptw":ptw,"floor":floor})
                    print(f"  📉 FLOOR_BLOCK {iid} ({model} {color}): cur=${cur} ptw=${ptw} floor=${floor}")
                else:
                    stats["untouched"] += 1
            else:
                stats["untouched"] += 1
        elif st == "not_listed":
            stats["not_listed"] += 1
        else:
            stats["untouched"] += 1
        time.sleep(0.15)
    except Exception as e:
        stats["errors"] += 1
        print(f"  ! err {iid}: {str(e)[:80]}")

# Reparto stock pool
pubs_by_pool = {}
for iid, m in cfg.items():
    k = (m.get("model"), m.get("color"))
    if k in POOL_SIZE: pubs_by_pool.setdefault(k, []).append(iid)
for key, total in POOL_SIZE.items():
    pubs = pubs_by_pool.get(key, [])
    if not pubs: continue
    n = len(pubs); per = total // n; rem = total - per*n
    for i, iid in enumerate(pubs):
        amt = per + (rem if i==0 else 0)
        cfg[iid]["real_stock"] = max(0, amt - 1)
        cfg[iid]["pool_total"] = total

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}\n=== RESUMEN ===")
print(f"Catalog items procesados: {len(catalog_items)}")
for k,v in stats.items(): print(f"  {k}: {v}")

if TG and TGCID:
    msg = f"🛠️ *Full War Pass — Raymundo*\n\n"
    msg += f"Items procesados: *{len(catalog_items)}*\n"
    for k,v in stats.items(): msg += f"• {k}: *{v}*\n"
    if fixed_list:
        msg += f"\n✅ Fixes aplicados ({len(fixed_list)}):\n"
        for f in fixed_list[:8]:
            msg += f"• `{f['iid']}` {f['st']}: ${f['old']:.0f}→${f['new']:.0f}\n"
    if floor_blocks:
        msg += f"\n📉 Floor blocks ({len(floor_blocks)}) — competidor < floor:\n"
        for f in floor_blocks[:8]:
            msg += f"• `{f['iid']}` {f['model']} {f['color']}: ptw=${f['ptw']:.0f} floor=${f['floor']}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
