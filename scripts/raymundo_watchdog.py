"""
RAYMUNDO WATCHDOG — corre cada 1 min, repausa cualquier item activo.
Loop interno 5×30s para coverage continuo.
"""
import os, requests, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

def get_token():
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    return r["access_token"]

def pause_pass(H, USER_ID):
    ids = []; offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    if not ids: return 0
    n = 0
    for iid in ids:
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10)
        if rp.status_code == 200:
            n += 1
            print(f"  [WATCHDOG] PAUSADO {iid}")
    return n

TOKEN = get_token()
H = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID = me["id"]
print(f"Watchdog Raymundo ({me.get('nickname')}) — loop 10×30s")

total = 0
for i in range(10):
    print(f"\n=== Iter {i+1}/10 ({time.strftime('%H:%M:%S')}) ===")
    try:
        n = pause_pass(H, USER_ID)
        total += n
        if n == 0: print(f"  todo pausado ✓")
    except Exception as e:
        print(f"  err: {e}")
        try: TOKEN = get_token(); H["Authorization"] = f"Bearer {TOKEN}"
        except: pass
    if i < 9: time.sleep(30)

print(f"\nTotal pausados en este run: {total}")
