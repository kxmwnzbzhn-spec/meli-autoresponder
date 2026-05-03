#!/usr/bin/env python3
"""ATAQUE FLOOR: bajar los 16 directo al FLOOR mínimo, sin ptw-1.
- Go 4 → $449 (FLOOR)
- Go 3 → $399 (FLOOR)
- Clip 5 → $699 (FLOOR)
Esto garantiza que ganemos a menos que el competidor también esté en floor.
Si seguimos perdiendo es porque el competidor está empatando floor → reportarlo.
"""
import os, requests, time

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

FLOORS = {"Go 4": 449, "Go 3": 399, "Clip 5": 699}

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}


def detect(t):
    t = (t or "").lower()
    if "clip 5" in t or "clip5" in t: return "Clip 5"
    if "go 4" in t or "go4" in t:     return "Go 4"
    if "go 3" in t or "go3" in t:     return "Go 3"
    return None


report = []
for iid in ITEMS:
    it = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                      headers=H, timeout=10,
                      params={"attributes":"id,title,price,status"}).json()
    title = it.get("title","")
    cur = it.get("price")
    model = detect(title)
    if not model:
        report.append({"iid":iid,"action":"unknown_model"})
        continue
    floor = FLOORS[model]

    # PTW check primero para diagnostico
    ptw_resp = requests.get(
        f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
        headers=H, timeout=8).json()
    st = ptw_resp.get("status")
    ptw = ptw_resp.get("price_to_win")

    # Go 3 forzar 399 (floor) en lugar de 499 — si está perdiendo necesita ataque
    target = floor

    if cur != target:
        pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                          headers=H, json={"price": target})
        ok = pr.status_code == 200
        print(f"  {'✅' if ok else '❌'} {iid} {model} ${cur}→${target} | st={st} ptw=${ptw}")
        report.append({"iid":iid,"model":model,"old":cur,"new":target,"st":st,"ptw":ptw,"ok":ok})
    else:
        print(f"  ✓ {iid} {model} ya en floor ${cur} | st={st} ptw=${ptw}")
        report.append({"iid":iid,"model":model,"cur":cur,"st":st,"ptw":ptw,"action":"already_floor"})
    time.sleep(0.25)

# Verificacion post-cambio: re-consultar ptw
print(f"\n=== VERIFICACION POST-CAMBIO ===")
time.sleep(3)
verif = []
for iid in ITEMS:
    it = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                      headers=H, timeout=10,
                      params={"attributes":"price"}).json()
    ptw_resp = requests.get(
        f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
        headers=H, timeout=8).json()
    cur = it.get("price")
    st = ptw_resp.get("status")
    ptw = ptw_resp.get("price_to_win")
    print(f"  {iid}: ${cur} st={st} ptw=${ptw}")
    verif.append({"iid":iid,"price":cur,"st":st,"ptw":ptw})
    time.sleep(0.2)

still_losing = [v for v in verif if v["st"] in ("losing","sharing","competing")]

if TG and TGCID:
    msg = f"🔥 *FLOOR ATTACK 16 — Raymundo*\n\n"
    ok_count = sum(1 for r in report if r.get("ok"))
    msg += f"Bajados a FLOOR: *{ok_count}*\n"
    msg += f"Ya en floor: *{sum(1 for r in report if r.get('action')=='already_floor')}*\n\n"
    msg += f"*Verificación post:*\n"
    msg += f"• Winning: *{sum(1 for v in verif if v['st']=='winning')}*\n"
    msg += f"• Sigue compitiendo: *{len(still_losing)}*\n\n"
    if still_losing:
        msg += f"⚠️ *Competidor matchea floor:*\n"
        for v in still_losing[:10]:
            msg += f"• `{v['iid']}` ${v['price']} st={v['st']} ptw=${v['ptw']}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
