#!/usr/bin/env python3
"""
Claribel daily reactivation at 12 PM CDMX:
- Si state.throttled = True, reactiva los items pausados por throttle
- Si NO había throttle, no hace nada (no reactivar items pausados manualmente por user)
- Limpia state.throttled
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

STATE_FILE = "claribel_throttle_state.json"

try: state = json.load(open(STATE_FILE))
except: state = {}

if not state.get("throttled"):
    print("No hay throttle activo — nada que reactivar")
    print(f"State: {state}")
    exit(0)

paused_items = state.get("items_paused", [])
print(f"Reactivando {len(paused_items)} items pausados ayer por throttle...\n")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

reactivated = []
errors = []
for iid in paused_items:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    if g.get("status") != "paused":
        print(f"  {iid} status={g.get('status')} — skip (ya no pausado)")
        continue
    qty = g.get("available_quantity",0)
    body = {"status":"active"}
    if qty == 0:
        body["available_quantity"] = 1
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json=body, timeout=15)
    if rp.status_code == 200:
        reactivated.append(iid)
        print(f"  ▶️  reactivado {iid}")
    else:
        errors.append((iid, rp.status_code, rp.text[:120]))
        print(f"  ❌ {iid} err {rp.status_code}")
    time.sleep(0.3)

# Clear throttle state but keep date counter (so we don't re-trigger same day)
from datetime import datetime, timezone, timedelta
cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
state["throttled"] = False
state["items_paused"] = []
state["sales_count"] = 0  # reset daily counter
state["date"] = cdmx.strftime("%Y-%m-%d")
state["last_reactivation"] = int(time.time())

json.dump(state, open(STATE_FILE,"w"), indent=2)

if TG_TOKEN and TG_CHAT:
    msg = (f"▶️ *Claribel reactivada* (12:00 PM CDMX)\n"
           f"Reactivados *{len(reactivated)}* items\n"
           f"Errores: *{len(errors)}*\n"
           f"Contador diario reset → 0/70")
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"})

print(f"\n✅ Reactivados: {len(reactivated)} | Errores: {len(errors)}")
