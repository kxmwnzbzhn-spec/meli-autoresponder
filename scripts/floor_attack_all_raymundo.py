#!/usr/bin/env python3
"""BARREDORA AGRESIVA RAYMUNDO: TODOS los catálogos NO winning → FLOOR directo.
- Go 4 → $449
- Go 3 → $399
- Clip 5 → $699

No ptw-1 (que se pierde por chase). Floor directo. Reporta cuántos siguen
perdiendo después del cambio (= competidor también en floor).
"""
import os, requests, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

FLOORS   = {"Go 4": 449, "Go 3": 399, "Clip 5": 699}
CEILINGS = {"Go 4": 699, "Go 3": 599, "Clip 5": 899}

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me["id"]
print(f"Cuenta {me['nickname']} ({uid})\n")


def detect(t):
    t = (t or "").lower()
    if "clip 5" in t or "clip5" in t: return "Clip 5"
    if "go 4" in t or "go4" in t:     return "Go 4"
    if "go 3" in t or "go3" in t:     return "Go 3"
    return None


# Listar TODOS los items active
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
    if not results or offset >= total: break
print(f"Active items: {len(all_iids)}")

# Bulk fetch
items_data = []
for i in range(0, len(all_iids), 20):
    chunk = all_iids[i:i+20]
    r = requests.get("https://api.mercadolibre.com/items",
                     headers=H, params={"ids":",".join(chunk),
                       "attributes":"id,title,price,catalog_listing,status"},
                     timeout=20).json()
    for resp in r:
        if resp.get("code") == 200:
            items_data.append(resp.get("body"))
    time.sleep(0.15)

catalog_items = [it for it in items_data
                 if it.get("catalog_listing") and it.get("status") == "active"]
print(f"Catalog items: {len(catalog_items)}\n")

stats = {"floor_dropped":0, "already_floor":0, "ceiling_capped":0,
         "winning_skip":0, "unknown":0, "errors":0, "still_competing":0}
losing_items = []
still_competing_after = []

for it in catalog_items:
    iid = it["id"]
    title = it.get("title","")
    cur = it.get("price")
    model = detect(title)
    if not model:
        stats["unknown"] += 1; continue
    floor = FLOORS[model]
    ceiling = CEILINGS[model]

    try:
        # Ceiling enforce
        if cur > ceiling:
            pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                              headers=H, json={"price": ceiling})
            if pr.status_code == 200:
                stats["ceiling_capped"] += 1
                cur = ceiling

        # PTW lookup
        ptw_resp = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=8).json()
        st = ptw_resp.get("status")
        ptw = ptw_resp.get("price_to_win")

        if st == "winning":
            stats["winning_skip"] += 1
            time.sleep(0.08)
            continue

        # NOT winning → atacar al floor
        if cur != floor:
            losing_items.append({"iid":iid,"model":model,"old":cur,"st":st,"ptw":ptw})
            pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                              headers=H, json={"price": floor})
            if pr.status_code == 200:
                stats["floor_dropped"] += 1
                print(f"  ⚡ FLOOR {model} {iid}: ${cur}→${floor} (st={st} ptw=${ptw})")
            else:
                stats["errors"] += 1
                print(f"  ❌ {iid}: {pr.status_code} {pr.text[:80]}")
        else:
            stats["already_floor"] += 1

        time.sleep(0.12)
    except Exception as e:
        stats["errors"] += 1
        print(f"  ! err {iid}: {str(e)[:80]}")

# Verificación post-cambio en los que bajamos
print(f"\n=== VERIFICACION POST-CAMBIO ({len(losing_items)} items) ===")
time.sleep(5)
for li in losing_items:
    iid = li["iid"]
    try:
        ptw_resp = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=8).json()
        st_after = ptw_resp.get("status")
        ptw_after = ptw_resp.get("price_to_win")
        if st_after in ("losing","sharing","competing"):
            stats["still_competing"] += 1
            still_competing_after.append({**li, "st_after":st_after, "ptw_after":ptw_after})
        time.sleep(0.1)
    except: pass

print(f"\n=== RESUMEN BARREDORA ===")
for k,v in stats.items(): print(f"  {k}: {v}")

if TG and TGCID:
    msg = f"⚡ *BARREDORA TOTAL Raymundo*\n\n"
    msg += f"📋 Catalog items: *{len(catalog_items)}*\n"
    msg += f"✅ Ya winning: *{stats['winning_skip']}*\n"
    msg += f"⚡ Bajados a floor: *{stats['floor_dropped']}*\n"
    msg += f"🔻 Ceiling capped: *{stats['ceiling_capped']}*\n"
    msg += f"= Ya en floor: *{stats['already_floor']}*\n"
    if stats['still_competing']:
        msg += f"\n⚠️ Sigue compitiendo después: *{stats['still_competing']}*\n"
        msg += "(competidor también en floor)\n"
        for s in still_competing_after[:8]:
            msg += f"• `{s['iid']}` {s['model']} st={s['st_after']} ptw=${s['ptw_after']}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
