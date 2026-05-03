#!/usr/bin/env python3
"""Forzar a ganar los 16 items reportados por user.
Audit cada uno + ajusta agresivamente al ptw-1 (respetando floor).
Reporta cualquier que NO se pueda ganar (floor block o sin ptw)."""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

ITEMS = [
    "MLM2904773889","MLM2904767861","MLM2904767821","MLM2904767787",
    "MLM2904710475","MLM2904704661","MLM2904704645","MLM2904704617",
    "MLM2904693275","MLM2904680413","MLM2904680397","MLM2904680377",
    "MLM2904680371","MLM2904680347","MLM2904680329","MLM2904680319",
]

FLOORS   = {"Go 4": 449, "Go 3": 399, "Clip 5": 699}
CEILINGS = {"Go 4": 699, "Go 3": 599, "Clip 5": 899}
GO3_FORCE = 499

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}


def detect_model(title):
    t = (title or "").lower()
    if "clip 5" in t or "clip5" in t: return "Clip 5"
    if "go 4" in t or "go4" in t:     return "Go 4"
    if "go 3" in t or "go3" in t:     return "Go 3"
    return None


report = []
for iid in ITEMS:
    print(f"\n=== {iid} ===")
    try:
        it = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                          headers=H, timeout=10,
                          params={"attributes":"id,title,price,status,catalog_listing"}).json()
        title = it.get("title","")
        cur = it.get("price")
        status = it.get("status")
        print(f"  title: {title[:70]}")
        print(f"  status: {status}, price: ${cur}")

        if status != "active":
            report.append({"iid":iid,"action":"skip_not_active","status":status})
            continue

        model = detect_model(title)
        if not model:
            report.append({"iid":iid,"action":"skip_unknown_model","title":title[:50]})
            continue

        floor = FLOORS[model]
        ceiling = CEILINGS[model]

        # Go 3 force
        if model == "Go 3":
            target = GO3_FORCE
            if cur != target:
                pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                  headers=H, json={"price": target})
                print(f"  📌 GO3 ${cur}→${target}: {pr.status_code}")
                report.append({"iid":iid,"model":model,"old":cur,"new":target,"action":"go3_force","ok":pr.status_code==200})
            continue

        # PTW
        ptw_resp = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=10).json()
        st = ptw_resp.get("status")
        ptw = ptw_resp.get("price_to_win")
        print(f"  ptw_status={st}, ptw=${ptw}")

        if ptw is None:
            # No data, intentar bajar al floor para asegurar visibilidad
            target = floor
            if cur != target:
                pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                                  headers=H, json={"price": target})
                print(f"  ⚠️ NO_PTW {model} {cur}→${target}: {pr.status_code}")
                report.append({"iid":iid,"model":model,"old":cur,"new":target,"action":"no_ptw_to_floor","ok":pr.status_code==200})
            continue

        target = max(floor, min(ceiling, round(ptw - 1, 0)))

        if target < floor:
            print(f"  📉 FLOOR BLOCK: ptw=${ptw} pero floor=${floor}")
            report.append({"iid":iid,"model":model,"cur":cur,"ptw":ptw,"floor":floor,"action":"floor_block"})
            continue

        if target == cur:
            print(f"  ✓ ya en target ${target}")
            report.append({"iid":iid,"model":model,"cur":cur,"ptw":ptw,"action":"already_target"})
            continue

        pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                          headers=H, json={"price": target})
        emoji = "✅" if pr.status_code == 200 else "❌"
        print(f"  {emoji} ${cur}→${target} (ptw=${ptw}): {pr.status_code}")
        report.append({"iid":iid,"model":model,"old":cur,"new":target,"ptw":ptw,"st":st,"action":"adjusted","ok":pr.status_code==200})
        time.sleep(0.3)
    except Exception as e:
        print(f"  ! err: {e}")
        report.append({"iid":iid,"action":"error","err":str(e)[:120]})

print(f"\n{'='*70}\n=== RESUMEN ===")
for r in report:
    print(f"  {r}")

# TG
if TG and TGCID:
    ok_count = sum(1 for r in report if r.get("ok"))
    block = [r for r in report if r["action"] in ("floor_block","skip_not_active","skip_unknown_model")]
    msg = f"🎯 *Force win 16 items reportados*\n\n"
    msg += f"Total: {len(report)}\n"
    msg += f"Acciones aplicadas: {ok_count}\n"
    msg += f"Bloqueados/sin acción: {len(block)}\n\n"
    for r in report[:20]:
        if r.get("ok"):
            msg += f"✅ `{r['iid']}` {r.get('model','?')}: ${r.get('old')}→${r.get('new')}\n"
        elif r["action"] == "floor_block":
            msg += f"📉 `{r['iid']}` {r.get('model')}: ptw=${r.get('ptw')} floor=${r.get('floor')}\n"
        elif r["action"] == "already_target":
            msg += f"✓ `{r['iid']}` {r.get('model')}: ya en ${r.get('cur')}\n"
        else:
            msg += f"⚠️ `{r['iid']}` {r['action']}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
