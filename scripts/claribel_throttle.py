#!/usr/bin/env python3
"""
Claribel daily sales throttle:
- Cuenta ventas globales del día (00:00 CDMX = 06:00 UTC)
- Si suma >= 70 unidades: pausa TODOS los items activos
- Estado en claribel_throttle_state.json
- Solo afecta Claribel, mantiene visibility para resto de cuentas
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

DAILY_LIMIT = 70
STATE_FILE = "claribel_throttle_state.json"

# CDMX = UTC-6
def cdmx_midnight_utc():
    """Get midnight CDMX (today at 00:00) as UTC timestamp."""
    now_utc = datetime.now(timezone.utc)
    cdmx = now_utc - timedelta(hours=6)
    midnight_cdmx = cdmx.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_cdmx + timedelta(hours=6)
    return midnight_utc

def cdmx_today_str():
    cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
    return cdmx.strftime("%Y-%m-%d")

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
USER_ID = me["id"]

# Load state
try: state = json.load(open(STATE_FILE))
except: state = {}

today = cdmx_today_str()
state_today = state.get("date") == today

# Reset state if new day
if not state_today:
    print(f"📅 Nuevo día {today} (anterior: {state.get('date')}). Reset throttle.")
    state = {"date": today, "throttled": False, "items_paused": [], "sales_count": 0}

# Count today's sales (orders since midnight CDMX)
midnight_utc = cdmx_midnight_utc()
date_from = midnight_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

print(f"Cuenta: {me.get('nickname')} ({USER_ID})")
print(f"Buscando ventas desde {date_from} CDMX-midnight ({today})\n")

total_qty = 0
offset = 0
order_ids = []
while True:
    rr = requests.get(
        f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",
        headers=H, timeout=20
    ).json()
    results = rr.get("results", [])
    if not results: break
    for o in results:
        # Only count paid orders
        if o.get("status") in ("paid","shipped","delivered"):
            for oi in o.get("order_items",[]):
                total_qty += oi.get("quantity",0)
            order_ids.append(o.get("id"))
    offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

print(f"Ventas hoy: *{total_qty}u* (límite {DAILY_LIMIT}) | {len(order_ids)} órdenes")
state["sales_count"] = total_qty

# If hit threshold and not yet throttled, pause everything
if total_qty >= DAILY_LIMIT and not state.get("throttled"):
    print(f"\n🚨 LÍMITE ALCANZADO ({total_qty}/{DAILY_LIMIT}) → pausando TODOS los items activos\n")
    
    # Get all active items
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
            print(f"  ⏸️  paused {iid}")
        else:
            print(f"  ❌ {iid} err {rp.status_code}")
        time.sleep(0.3)
    
    state["throttled"] = True
    state["items_paused"] = paused
    state["throttled_at"] = int(time.time())
    
    if TG_TOKEN and TG_CHAT:
        msg = (f"🚨 *Claribel throttle ACTIVO*\n"
               f"Ventas hoy: *{total_qty}u* (límite {DAILY_LIMIT})\n"
               f"Pausados *{len(paused)}* items.\n"
               f"Reactivación automática mañana 12:00 PM CDMX.")
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"})
elif state.get("throttled"):
    print(f"\n⏸️  Throttle YA activo (pausados {len(state.get('items_paused',[]))} items, ventas hoy {total_qty})")
else:
    print(f"\n✅ Throttle OFF — {DAILY_LIMIT - total_qty}u disponibles")

json.dump(state, open(STATE_FILE,"w"), indent=2)
print(f"\nState saved: {state}")
