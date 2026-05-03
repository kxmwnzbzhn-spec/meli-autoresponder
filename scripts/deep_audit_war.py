#!/usr/bin/env python3
"""Deep audit + fix Raymundo:

Para CADA item de catalog_war activo:
1. Consulta ptw (price_to_win)
2. Si losing/sharing: forzar precio a ptw-1 (respetando floor)
3. Si Go 3: setear todos a $499 mínimo (target del user)
4. Si Go 4: floor $449
5. Si Clip 5: floor $799
6. Reportar floor-blocks (donde competidor está debajo de nuestro floor)

NUEVOS DEFAULTS por modelo:
- Go 4:    floor 449 / target 499
- Go 3:    floor 349 / FORCE 499 (user request)
- Clip 5:  floor 799
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

FLOORS = {"Go 4": 449, "Go 3": 349, "Clip 5": 799}
GO3_FORCE_PRICE = 499  # user pidio: toda Go 3 = $499
CEILING = 1499

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token", "client_id": APP_ID,
    "client_secret": APP_SECRET, "refresh_token": RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}",
     "Content-Type": "application/json"}

with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)


def detect(title):
    t = (title or "").lower().replace("bluetooth", " ")
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


war_iids = [iid for iid, m in cfg.items() if m.get("catalog_war")]
print(f"Items con catalog_war=True: {len(war_iids)}\n")

stats = {"total": 0, "winning": 0, "sharing": 0, "not_listed": 0, "losing": 0,
         "fixed": 0, "floor_block": 0, "no_data": 0, "go3_set": 0,
         "errors": 0, "skipped_inactive": 0}
fixed_list = []
floor_block_list = []

for iid in war_iids:
    meta = cfg[iid]
    stats["total"] += 1
    try:
        # State
        it = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                          headers=H, timeout=10,
                          params={"attributes": "id,title,price,status,catalog_listing"}).json()
        if it.get("status") != "active":
            stats["skipped_inactive"] += 1
            continue
        cur = it.get("price")
        title = it.get("title", "")

        # Re-detect model si falta
        if not meta.get("model"):
            m, c = detect(title)
            if m:
                meta["model"] = m
            if c:
                meta["color"] = c

        model = meta.get("model")
        floor = FLOORS.get(model, meta.get("floor_price", 199))
        meta["floor_price"] = floor
        meta["ceiling_price"] = CEILING

        # === GO 3 = $499 fijo ===
        if model == "Go 3":
            if cur != GO3_FORCE_PRICE:
                pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                  headers=H, json={"price": GO3_FORCE_PRICE})
                if pr.status_code == 200:
                    stats["go3_set"] += 1
                    print(f"  📌 GO3 SET {iid}: ${cur}→${GO3_FORCE_PRICE}")
                else:
                    print(f"  ⚠️ GO3 PUT err {iid}: {pr.text[:120]}")
            cfg[iid] = meta
            time.sleep(0.15)
            continue

        # === Otros: ptw logic ===
        ptw_resp = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=8).json()
        st = ptw_resp.get("status")
        ptw = ptw_resp.get("price_to_win")

        if st == "winning":
            stats["winning"] += 1
            # CAP a ptw-1 si estamos por encima
            if ptw is not None and cur > ptw - 1:
                target = max(floor, round(ptw - 1, 0))
                if target < cur:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        print(f"  🛡️ CAP {iid}: ${cur}→${target} (ptw=${ptw})")
                        stats["fixed"] += 1
        elif st == "sharing":
            stats["sharing"] += 1
            # Para sharing, intentar bajar $1 abajo de ptw
            if ptw is not None:
                target = max(floor, round(ptw - 1, 0))
                if target < cur and target >= floor:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        stats["fixed"] += 1
                        fixed_list.append({"iid":iid,"old":cur,"new":target,"ptw":ptw,"status":"sharing"})
                        print(f"  ✅ FIX SHARING {iid}: ${cur}→${target}")
        elif st in ("losing", "competing"):
            stats["losing"] += 1
            if ptw is not None:
                target = max(floor, round(ptw - 1, 0))
                if target < cur and target >= floor:
                    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                      headers=H, json={"price": target})
                    if pr.status_code == 200:
                        stats["fixed"] += 1
                        fixed_list.append({"iid":iid,"old":cur,"new":target,"ptw":ptw,"status":"losing"})
                        print(f"  ✅ FIX LOSING {iid}: ${cur}→${target}")
                else:
                    stats["floor_block"] += 1
                    floor_block_list.append({"iid":iid,"label":meta.get("label","?"),
                                              "cur":cur,"ptw":ptw,"floor":floor})
                    print(f"  📉 FLOOR BLOCK {iid}: cur=${cur} ptw=${ptw} floor=${floor}")
        elif st == "not_listed":
            stats["not_listed"] += 1
        else:
            stats["no_data"] += 1

        cfg[iid] = meta
        time.sleep(0.15)
    except Exception as e:
        stats["errors"] += 1
        print(f"  ! err {iid}: {str(e)[:100]}")

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}\n=== RESUMEN ===")
for k, v in stats.items():
    print(f"  {k}: {v}")

if TG and TGCID:
    msg = "🛠️ *Deep audit war Raymundo*\n\n"
    for k, v in stats.items():
        msg += f"• {k}: *{v}*\n"
    if fixed_list:
        msg += f"\n✅ Bajados ahora ({len(fixed_list)}):\n"
        for f in fixed_list[:10]:
            msg += f"• `{f['iid']}`: ${f['old']:.0f}→${f['new']:.0f}\n"
    if floor_block_list:
        msg += f"\n📉 Floor block ({len(floor_block_list)}) — competidor abajo de nuestro mínimo:\n"
        for f in floor_block_list[:10]:
            msg += f"• `{f['iid']}` {f['label'][:25]}: ptw=${f['ptw']:.0f} floor=${f['floor']}\n"
    if stats["go3_set"]:
        msg += f"\n📌 Go 3 fijados a \\${GO3_FORCE_PRICE}: {stats['go3_set']}"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown", "text": msg[:4000]}, timeout=20)
