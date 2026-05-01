#!/usr/bin/env python3
"""
Reactivar Raymundo a las 6 AM CDMX cada día:
- Resetea sales_count a 0
- throttled=false, items_paused=[]
- Reactiva TODOS los items pausados con qty=1
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

# 1. Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
tok = r["access_token"]; uid = r["user_id"]
H = {"Authorization":f"Bearer {tok}","Content-Type":"application/json"}
print(f"[Raymundo 6AM] uid={uid}")

# 2. Listar pausados
ids = []
off = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=paused&limit=50&offset={off}", headers=H, timeout=15).json()
    res = j.get("results", [])
    if not res: break
    ids.extend(res); off += 50
    if off > 5000: break
print(f"  paused: {len(ids)}")

# 3. Reactivar con qty=1
reactivated = 0
errors = []
for iid in ids:
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"status":"active","available_quantity":1}, timeout=15)
    if rp.status_code == 200:
        reactivated += 1
    else:
        errors.append((iid, rp.status_code))
    time.sleep(0.15)
print(f"  reactivados: {reactivated} / errores: {len(errors)}")

# 4. Reset state
today = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d")
try: state = json.load(open("multi_throttle_state.json"))
except: state = {"accounts": {}}
state.setdefault("accounts", {})["RAYMUNDO"] = {
    "date": today, "throttled": False, "items_paused": [], "sales_count": 0
}
state["last_raymundo_6am_reactivate"] = int(time.time())
with open("multi_throttle_state.json","w") as f:
    json.dump(state, f, indent=2)
print(f"  state reset: RAYMUNDO sales_count=0, throttled=false")

# 5. Telegram
if TG_TOKEN and TG_CHAT:
    msg = f"☀️ <b>Raymundo reactivado 6 AM</b>\\n\\n• Items reactivados: {reactivated}\\n• Errores: {len(errors)}\\n• Cap hoy: 200 u\\n• sales_count reset: 0"
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={
        "chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"
    }, timeout=10)

