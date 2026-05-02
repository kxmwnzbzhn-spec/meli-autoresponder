"""Watchdog: pausa todo lo activo de Raymundo cada 60s durante 30 min."""
import os, requests, time

def get_token():
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
    }).json()
    return r["access_token"]

iters = 30  # 30 ciclos x 60s = 30 min
for i in range(iters):
    try:
        tok = get_token()
        H = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
        sid = me["id"]
        # Buscar items activos
        ids = []
        s = 0
        while True:
            d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}", headers=H, timeout=15).json()
            got = d.get("results", [])
            if not got: break
            ids.extend(got)
            s += 100
            if s >= d.get("paging",{}).get("total",0): break
        paused = 0
        for iid in ids:
            r = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"status":"paused"}, timeout=10)
            if r.status_code in (200,201): paused += 1
        print(f"[{i+1}/{iters}] activos={len(ids)} pausados={paused}")
    except Exception as e:
        print(f"[{i+1}/{iters}] err: {e}")
    time.sleep(55)

# Telegram al final
tg_t = os.environ.get("TELEGRAM_BOT_TOKEN"); tg_c = os.environ.get("TELEGRAM_CHAT_ID")
if tg_t and tg_c:
    requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage",
        data={"chat_id":tg_c, "text":f"🛑 Raymundo watchdog completado: {iters} ciclos / 30 min"}, timeout=10)
