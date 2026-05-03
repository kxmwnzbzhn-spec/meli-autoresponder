import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me['id']

# Listar paused y closed
for status in ("paused","closed"):
    r = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search",
                     headers=H, params={"status":status,"limit":100,"offset":0},
                     timeout=20).json()
    iids = r.get("results",[])
    total = r.get("paging",{}).get("total",0)
    print(f"\n=== {status} (total {total}, primeros {len(iids)}) ===")
    if iids:
        # Get titles
        for i in range(0, min(len(iids),50), 20):
            chunk = iids[i:i+20]
            rr = requests.get("https://api.mercadolibre.com/items",
                              headers=H, params={"ids":",".join(chunk),
                                "attributes":"id,title,price,sub_status,available_quantity,date_closed"},
                              timeout=20).json()
            for resp in rr:
                if resp.get("code")==200:
                    it = resp["body"]
                    sub = it.get("sub_status","")
                    print(f"  {it.get('id')} qty={it.get('available_quantity')} sub={sub} closed={it.get('date_closed')} | {it.get('title','')[:60]}")

print("\n=== REACTIVAR todos los paused ===")
# Listar todos paused
r = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search",
                 headers=H, params={"status":"paused","limit":100,"offset":0},
                 timeout=20).json()
paused = r.get("results",[])
reactivated = 0
for iid in paused[:50]:
    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                      json={"status":"active","available_quantity":1})
    if pr.status_code == 200:
        reactivated += 1
    else:
        print(f"  ⚠️ {iid}: {pr.text[:120]}")
print(f"\nReactivados: {reactivated} de {len(paused)}")

if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown",
        "text":f"🔄 Reactivadas *{reactivated}* publicaciones pausadas en Raymundo"
    }, timeout=20)
