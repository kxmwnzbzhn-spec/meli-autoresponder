#!/usr/bin/env python3
"""
Multi-account daily sales throttle.
- Cuentas: Juan, Claribel, Raymundo, Dilcie, Mildred (NO ASVA)
- Por cada cuenta: cuenta ventas globales del día desde 00:00 CDMX
- Si suma >= 70 unidades: pausa TODOS los items activos de esa cuenta
- Estado por cuenta en multi_throttle_state.json
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

# CUENTAS QUE TIENEN THROTTLE (ASVA EXCLUIDA — cuenta madura sin límite)
THROTTLED_ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN", 70),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL", 70),  # base, override por ramp_day
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO", 50),  # Cap 50/día,
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE", 70),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED", 70),
]

# Claribel ramp-up: 70 hoy, 80 mañana, 90 después, 100, 150
CLARIBEL_RAMP = [70, 80, 90, 100, 150]

STATE_FILE = "multi_throttle_state.json"

def cdmx_midnight_utc():
    now_utc = datetime.now(timezone.utc)
    cdmx = now_utc - timedelta(hours=6)
    midnight_cdmx = cdmx.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight_cdmx + timedelta(hours=6)

def cdmx_today():
    return (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d")

# Load state
try: state = json.load(open(STATE_FILE))
except: state = {"accounts": {}}
if "accounts" not in state: state["accounts"] = {}

today = cdmx_today()
date_from = cdmx_midnight_utc().strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"Throttle check {today} (desde {date_from})\n")

tg_alerts = []

for label, env_var, daily_limit in THROTTLED_ACCOUNTS:
    # Claribel ramp-up
    if label == "CLARIBEL":
        ramp_day = state.get("claribel_ramp_day", 0)
        ramp_idx = min(ramp_day, len(CLARIBEL_RAMP)-1)
        daily_limit = CLARIBEL_RAMP[ramp_idx]
        print(f"  Claribel ramp_day={ramp_day} → límite {daily_limit}u")
    RT = os.environ.get(env_var, "")
    if not RT:
        print(f"[{label}] sin token — skip"); continue
    
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        print(f"[{label}] auth err: {e}"); continue
    
    # Reset state if new day for this account
    acct_state = state["accounts"].get(label, {})
    if acct_state.get("date") != today:
        acct_state = {"date": today, "throttled": False, "items_paused": [], "sales_count": 0}
    
    # Count today's sales
    total_qty = 0
    offset = 0
    while True:
        rr = requests.get(
            f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",
            headers=H, timeout=20
        ).json()
        results = rr.get("results", [])
        if not results: break
        for o in results:
            if o.get("status") in ("paid","shipped","delivered"):
                for oi in o.get("order_items",[]):
                    total_qty += oi.get("quantity", 0)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    acct_state["sales_count"] = total_qty
    print(f"=== {label} ({me.get('nickname')}): {total_qty}/{daily_limit}u ===")
    
    if total_qty >= daily_limit and not acct_state.get("throttled"):
        print(f"  🚨 LÍMITE ALCANZADO → pausando todos los items activos")
        item_ids = []
        offset = 0
        while True:
            rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}", headers=H, timeout=15).json()
            b = rr.get("results",[])
            if not b: break
            item_ids.extend(b); offset += 50
            if offset >= rr.get("paging",{}).get("total",0): break
        
        paused = []
        for iid in item_ids:
            rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"status":"paused"}, timeout=15)
            if rp.status_code == 200:
                paused.append(iid)
            time.sleep(0.2)
        
        acct_state["throttled"] = True
        acct_state["items_paused"] = paused
        acct_state["throttled_at"] = int(time.time())
        print(f"  ⏸️  Pausados {len(paused)} items")
        tg_alerts.append(f"🚨 *{label} throttled* {total_qty}/{daily_limit}u — pausados {len(paused)} items")
    elif acct_state.get("throttled"):
        print(f"  ⏸️  Ya throttled (pausados {len(acct_state.get('items_paused',[]))})")
    else:
        print(f"  ✅ OK — {daily_limit - total_qty}u disponibles")
    
    state["accounts"][label] = acct_state

state["last_run"] = int(time.time())
state["last_run_date"] = today
json.dump(state, open(STATE_FILE,"w"), indent=2, ensure_ascii=False)

if TG_TOKEN and TG_CHAT and tg_alerts:
    msg = "\n".join(tg_alerts) + "\n\nReactivación automática mañana 12:00 PM CDMX."
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"})
