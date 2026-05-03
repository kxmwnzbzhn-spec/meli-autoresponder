#!/usr/bin/env python3
"""Cierra item MLM2904693387 (no es bocina, es caja de almacenamiento)
y lo quita del stock_config_raymundo + redistribuye stock pool Negro."""
import os, requests, json

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

BAD_IID = "MLM2904693387"
BAD_CPID = "MLM59907169"  # catálogo "caja de almacenamiento"

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}

# 1) Cerrar item
print(f"=== Cerrando {BAD_IID} ===")
pr = requests.put(f"https://api.mercadolibre.com/items/{BAD_IID}", headers=H,
                  json={"status":"closed"})
print(f"  PUT status=closed → {pr.status_code}")
if pr.status_code != 200:
    print(f"  body: {pr.text[:300]}")

# 2) Limpiar stock_config y redistribuir Negro pool
with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)

if BAD_IID in cfg:
    del cfg[BAD_IID]
    print(f"  removido del stock_config")

# Redistribuir Negro pool 130 entre las publicaciones restantes
negro_pubs = [iid for iid, m in cfg.items() if m.get("model")=="Go 4" and m.get("color")=="Negro"]
print(f"\nGo 4 Negro pubs restantes: {len(negro_pubs)}")
total = 130
n = len(negro_pubs)
if n:
    per = total // n
    rem = total - per * n
    for i, iid in enumerate(negro_pubs):
        amt = per + (rem if i == 0 else 0)
        cfg[iid]["real_stock"] = amt - cfg[iid].get("min_visible", 1)
        cfg[iid]["pool_total"] = total
    print(f"  reparto: {per}u c/u (resto {rem})")

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

# Telegram
if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown",
        "text": (
            f"🧹 *Limpieza item incorrecto*\n\n"
            f"`{BAD_IID}` cerrado (era catálogo `{BAD_CPID}` = "
            f"caja de almacenamiento, no bocina).\n\n"
            f"Stock Negro redistribuido entre {n} pubs restantes."
        )}, timeout=20)
print("done")
