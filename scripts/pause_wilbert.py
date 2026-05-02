import os, requests, time
r = requests.post("https://api.mercadolibre.com/oauth/token", data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_WILBERT"]}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
sid = me["id"]
print(f"WILBERT id={sid} nick={me.get('nickname')}")

ids = []
s = 0
while True:
    d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}", headers=H, timeout=20).json()
    got = d.get("results", [])
    if not got:
        break
    ids.extend(got)
    s += 100
    if s >= d.get("paging", {}).get("total", 0):
        break
print(f"Items activos a pausar: {len(ids)}")

paused = err = 0
for iid in ids:
    rr = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"status":"paused"}, timeout=15)
    if rr.status_code in (200, 201):
        paused += 1
    else:
        err += 1
        print(f"  ERR {iid}: {rr.status_code} {rr.text[:80]}")
    time.sleep(0.25)
print(f"=== {paused} pausados / {err} errores ===")

tg_t = os.environ.get("TELEGRAM_BOT_TOKEN")
tg_c = os.environ.get("TELEGRAM_CHAT_ID")
if tg_t and tg_c:
    requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage", data={"chat_id":tg_c,"text":f"WILBERT pausado: {paused} items / {err} errores"}, timeout=10)
