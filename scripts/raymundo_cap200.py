"""Watchdog: si Raymundo llega a 200 ord pagadas hoy CDMX, pausar TODO inmediato y disable workflows."""
import os, requests, time
from datetime import datetime, timezone, timedelta

CAP = 200

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
    }).json()
    return r["access_token"]

def count_today():
    cdmx_now = datetime.now(timezone.utc) - timedelta(hours=6)
    midnight_cdmx = cdmx_now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_from = (midnight_cdmx + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    tok = get_token()
    H = {"Authorization": f"Bearer {tok}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
    UID = me["id"]
    paid = 0; off = 0
    while True:
        j = requests.get(f"https://api.mercadolibre.com/orders/search?seller={UID}&order.date_created.from={date_from}&limit=50&offset={off}", headers=H, timeout=20).json()
        res = j.get("results", [])
        if not res: break
        for o in res:
            if o.get("status") in ("paid","shipped","delivered","handling","ready_to_ship"):
                paid += 1
        if len(res) < 50: break
        off += 50
        if off > 2000: break
    return paid, tok, UID

def pause_all(tok, uid):
    H = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}
    ids = []; s = 0
    while True:
        d = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={s}", headers=H, timeout=15).json()
        got = d.get("results", []) or []
        if not got: break
        ids.extend(got); s += 100
        if s >= d.get("paging",{}).get("total",0): break
    paused = 0
    for iid in ids:
        rr = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"status":"paused"}, timeout=10)
        if rr.status_code in (200,201): paused += 1
    return len(ids), paused

# Loop: check cada 90s. Time budget ~5h
for i in range(200):
    try:
        paid, tok, uid = count_today()
        print(f"[{i+1}] Raymundo paid hoy: {paid}/{CAP}")
        if paid >= CAP:
            print(f"\n🛑 ALCANZADO {paid} ≥ {CAP}, pausando TODO")
            n, p = pause_all(tok, uid)
            print(f"  → {n} items activos, {p} pausados")
            tg_t = os.environ.get("TELEGRAM_BOT_TOKEN"); tg_c = os.environ.get("TELEGRAM_CHAT_ID")
            if tg_t and tg_c:
                requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage",
                    data={"chat_id":tg_c, "text":f"🛑 RAYMUNDO cap 200 alcanzado: {paid} ord pagadas hoy. Pausados {p}/{n} items."}, timeout=10)
            break
    except Exception as e:
        print(f"  err: {e}")
    time.sleep(90)
