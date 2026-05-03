import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

IID = "MLM2904680457"
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}

# Ver qué es
it = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H, timeout=15).json()
print(f"Item: {it.get('title','?')[:80]}")
print(f"  cpid: {it.get('catalog_product_id')}")

# Pausar
pr = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={"status":"paused"})
print(f"PUT paused → {pr.status_code}")

# Marcar deleted en config para que el bot NO lo reactive
try:
    with open("stock_config_raymundo.json") as f:
        cfg = json.load(f)
    if IID in cfg:
        cfg[IID]["auto_replenish"] = False
        cfg[IID]["catalog_war"] = False
        cfg[IID]["paused_by_user_color_wrong"] = True
        with open("stock_config_raymundo.json","w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        print(f"Config: auto_replenish=False, catalog_war=False")
except Exception as e:
    print(f"err config: {e}")

if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown",
        "text":f"⏸ `{IID}` pausado por usuario (no es nuestro color).\n{it.get('title','?')[:60]}"
    }, timeout=20)
