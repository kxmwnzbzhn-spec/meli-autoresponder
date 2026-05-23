#!/usr/bin/env python3
"""WAR UNIVERSAL — fuerza la barredora en TODA publicacion de catalogo activa
en Raymundo, NO importa si esta en cfg o no.

Reglas FORZADAS por modelo (independiente de cfg):
- Go 4:    floor 449, ceiling 699
- Go 3:    floor 399, ceiling 599, FORCE 499
- Clip 5:  floor 699, ceiling 899

Lógica por item:
1. Si cur > ceiling → bajar a ceiling
2. Si cur < floor   → subir a floor
3. Si Go 3 → forzar a 499
4. Sino, consultar ptw:
   - winning + cur > ptw-1 → cap a max(floor, ptw-1)
   - sharing/losing → bajar a max(floor, ptw-1)
   - si ptw < floor → quedarse en floor
"""
import os, requests, json, time
import meli_token

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

FLOORS   = {"Go 4": 449, "Go 3": 399, "Clip 5": 699}
CEILINGS = {"Go 4": 699, "Go 3": 599, "Clip 5": 899}
GO3_FORCE = 499

# Cargar floors per-item del config (override del modelo)
ITEM_FLOORS = {}
try:
    import json as _json
    with open("stock_config_raymundo.json") as _f:
        _cfg = _json.load(_f)
    for _iid, _meta in _cfg.items():
        if _meta.get("floor_locked_by_user") and _meta.get("floor_price"):
            ITEM_FLOORS[_iid] = _meta["floor_price"]
    if ITEM_FLOORS:
        print(f"[CFG] Item-level floors locked: {ITEM_FLOORS}")
except Exception as _e:
    print(f"[CFG] no item floors loaded: {_e}")

r = meli_token.refresh(RT)
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me['id']
print(f"Cuenta: {me['nickname']} ({uid})\n")


def detect_model(title):
    t = (title or "").lower()
    if "clip 5" in t or "clip5" in t: return "Clip 5"
    if "go 4" in t or "go4" in t:     return "Go 4"
    if "go 3" in t or "go3" in t:     return "Go 3"
    return None


# Listar TODOS los items active
print("Fetching all active items...")
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
print(f"Active items: {len(all_iids)}")

# Bulk fetch state
items_data = []
for i in range(0, len(all_iids), 20):
    chunk = all_iids[i:i+20]
    r = requests.get("https://api.mercadolibre.com/items",
                     headers=H, params={"ids":",".join(chunk),
                       "attributes":"id,title,price,catalog_listing,catalog_product_id,status"},
                     timeout=20).json()
    for resp in r:
        if resp.get("code") == 200:
            items_data.append(resp.get("body"))
    time.sleep(0.2)

catalog_items = [it for it in items_data
                 if it.get("catalog_listing") and it.get("status") == "active"]
print(f"Catalog active items: {len(catalog_items)}\n")

stats = {"total": len(catalog_items),
         "ceiling_dropped": 0, "floor_raised": 0,
         "go3_force": 0, "winning_cap": 0, "fixed_losing": 0,
         "skipped_unknown_model": 0, "no_action": 0, "errors": 0}
fixed_list = []

for it in catalog_items:
    iid = it["id"]
    title = it.get("title","")
    cur = it.get("price")
    model = detect_model(title)

    if not model:
        stats["skipped_unknown_model"] += 1
        print(f"  ❓ SKIP {iid} (modelo desconocido): {title[:50]}")
        continue

    floor = ITEM_FLOORS.get(iid, FLOORS[model])
    ceiling = CEILINGS[model]

    try:
        # === GO 3: forzar a $499 (ya está en rango 399-599) ===
        if model == "Go 3":
            if cur != GO3_FORCE:
                pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                  headers=H, json={"price": GO3_FORCE})
                if pr.status_code == 200:
                    stats["go3_force"] += 1
                    print(f"  📌 GO3 {iid}: ${cur}→${GO3_FORCE}")
                else:
                    print(f"  ⚠️ GO3 PUT err {iid}: {pr.text[:100]}")
            time.sleep(0.12)
            continue

        # === CEILING enforcement ===
        if cur > ceiling:
            pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                              headers=H, json={"price": ceiling})
            if pr.status_code == 200:
                stats["ceiling_dropped"] += 1
                print(f"  ⬇️ CEILING {model} {iid}: ${cur}→${ceiling}")
                cur = ceiling
            else:
                stats["errors"] += 1
                print(f"  ⚠️ CEILING err {iid}: {pr.text[:100]}")
                time.sleep(0.12)
                continue

        # === FLOOR enforcement ===
        if cur < floor:
            pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                              headers=H, json={"price": floor})
            if pr.status_code == 200:
                stats["floor_raised"] += 1
                print(f"  ⬆️ FLOOR {model} {iid}: ${cur}→${floor}")
                cur = floor

        # === PTW logic ===
        ptw_resp = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=8).json()
        st = ptw_resp.get("status")
        ptw = ptw_resp.get("price_to_win")

        if ptw is None:
            stats["no_action"] += 1
        else:
            target = max(floor, min(ceiling, round(ptw - 1, 0)))
            if st == "winning":
                if cur > target:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        stats["winning_cap"] += 1
                        print(f"  🛡️ CAP {iid}: ${cur}→${target} (ptw=${ptw})")
                    else:
                        stats["errors"] += 1
                else:
                    stats["no_action"] += 1
            elif st in ("losing", "sharing", "competing"):
                if target < cur:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        stats["fixed_losing"] += 1
                        fixed_list.append({"iid":iid,"old":cur,"new":target,"ptw":ptw,"st":st})
                        print(f"  ✅ FIX {st} {iid}: ${cur}→${target} (ptw=${ptw})")
                    else:
                        stats["errors"] += 1
                else:
                    stats["no_action"] += 1
            else:
                stats["no_action"] += 1

        time.sleep(0.12)
    except Exception as e:
        stats["errors"] += 1
        print(f"  ! err {iid}: {str(e)[:80]}")

print(f"\n{'='*60}\n=== RESUMEN ===")
for k, v in stats.items():
    print(f"  {k}: {v}")

if TG and TGCID:
    msg = "🛠️ *War UNIVERSAL Raymundo*\n\n"
    for k, v in stats.items():
        msg += f"• {k}: *{v}*\n"
    if fixed_list:
        msg += f"\n✅ FIX losing/sharing ({len(fixed_list)}):\n"
        for f in fixed_list[:10]:
            msg += f"• `{f['iid']}` {f['st']}: ${f['old']:.0f}→${f['new']:.0f}\n"
    msg += f"\n*Reglas:* Go4 449/699 • Go3 399/{GO3_FORCE}/599 • Clip5 699/899"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
