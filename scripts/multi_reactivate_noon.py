#!/usr/bin/env python3
"""
Multi-account reactivation at 12 PM CDMX.
Reactiva los items pausados por throttle en todas las cuentas (NO ASVA).
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

THROTTLED_ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    # ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),  # FROZEN
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
    ("BREN", "MELI_REFRESH_TOKEN_BREN"),
]
STATE_FILE = "multi_throttle_state.json"

try: state = json.load(open(STATE_FILE))
except: state = {"accounts": {}}

today_cdmx = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d")
tg_lines = ["▶️ *Reactivación 12:00 PM CDMX*"]
total_reactivated = 0

for label, env_var in THROTTLED_ACCOUNTS:
    acct_state = state.get("accounts", {}).get(label, {})
    if not acct_state.get("throttled"):
        print(f"[{label}] sin throttle — reset contador")
        state.setdefault("accounts", {})[label] = {"date": today_cdmx, "throttled": False, "items_paused": [], "sales_count": 0}
        continue
    
    paused_items = acct_state.get("items_paused", [])
    print(f"\n=== {label}: reactivando {len(paused_items)} items ===")
    
    RT = os.environ.get(env_var, "")
    if not RT:
        print(f"  sin token — skip"); continue
    
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
    
    reactivated = 0
    for iid in paused_items:
        g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
        if g.get("status") != "paused":
            continue
        body = {"status":"active"}
        if g.get("available_quantity",0) == 0:
            body["available_quantity"] = 1
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json=body, timeout=15)
        if rp.status_code == 200:
            reactivated += 1
        time.sleep(0.2)
    
    print(f"  ▶️  {reactivated} reactivados")
    total_reactivated += reactivated
    tg_lines.append(f"• {label}: {reactivated} items reactivados")
    
    # Reset state for this account
    state["accounts"][label] = {"date": today_cdmx, "throttled": False, "items_paused": [], "sales_count": 0}
    # Claribel ramp-up: incrementar día
    if label == "CLARIBEL":
        ramp_day = state.get("claribel_ramp_day", 0) + 1
        state["claribel_ramp_day"] = ramp_day
        ramp_seq = [70, 80, 90, 100, 150]
        ramp_idx = min(ramp_day, len(ramp_seq)-1)
        new_limit = ramp_seq[ramp_idx]
        print(f"  ⬆️  Claribel ramp_day → {ramp_day} (límite hoy: {new_limit}u)")

state["last_reactivation"] = int(time.time())
json.dump(state, open(STATE_FILE,"w"), indent=2, ensure_ascii=False)

if TG_TOKEN and TG_CHAT and total_reactivated > 0:
    tg_lines.append(f"\nContador diario reset → 0/70")
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":"\n".join(tg_lines),"parse_mode":"Markdown"})

print(f"\n✅ Total reactivados: {total_reactivated}")
