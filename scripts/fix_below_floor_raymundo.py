#!/usr/bin/env python3
"""Detectar y subir al floor cualquier item de Raymundo que este DEBAJO del floor.
Esto elimina canibalizacion interna (publicaciones nuestras peleando entre si).
"""
import os, requests, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

FLOORS = {"Go 4": 449, "Go 3": 399, "Clip 5": 699}

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me["id"]

def detect(t):
    t = (t or "").lower()
    if "clip 5" in t or "clip5" in t: return "Clip 5"
    if "go 4" in t or "go4" in t:     return "Go 4"
    if "go 3" in t or "go3" in t:     return "Go 3"
    return None

# Listar TODO active
all_iids = []
offset = 0
while True:
    r = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search",
                     headers=H, params={"status":"active","limit":100,"offset":offset},
                     timeout=20).json()
    results = r.get("results",[])
    all_iids.extend(results)
    total = r.get("paging",{}).get("total",0)
    offset += len(results)
    if not results or offset >= total: break

print(f"Active items: {len(all_iids)}")
items = []
for i in range(0, len(all_iids), 20):
    chunk = all_iids[i:i+20]
    r = requests.get("https://api.mercadolibre.com/items",
                     headers=H, params={"ids":",".join(chunk),
                       "attributes":"id,title,price,catalog_listing,status"},
                     timeout=20).json()
    for resp in r:
        if resp.get("code") == 200:
            items.append(resp.get("body"))
    time.sleep(0.15)

below = []
for it in items:
    if it.get("status") != "active": continue
    title = it.get("title","")
    cur = it.get("price")
    model = detect(title)
    if not model: continue
    floor = FLOORS[model]
    if cur < floor:
        below.append({"iid":it["id"],"title":title[:60],"model":model,"cur":cur,"floor":floor,
                      "catalog":bool(it.get("catalog_listing"))})

print(f"\n=== Items DEBAJO del floor: {len(below)} ===")
for b in below:
    print(f"  {b['iid']} {b['model']} ${b['cur']} → ${b['floor']} (cat={b['catalog']}) {b['title']}")

# Subirlos al floor
fixed = []
errs = []
for b in below:
    pr = requests.put(f"https://api.mercadolibre.com/items/{b['iid']}",
                      headers=H, json={"price": b["floor"]})
    ok = pr.status_code == 200
    if ok:
        fixed.append(b)
        print(f"  ⬆️ {b['iid']}: ${b['cur']}→${b['floor']}")
    else:
        errs.append({**b,"err":pr.text[:80]})
        print(f"  ❌ {b['iid']}: {pr.status_code} {pr.text[:80]}")
    time.sleep(0.15)

print(f"\n=== RESUMEN ===")
print(f"Below floor: {len(below)}, Fixed: {len(fixed)}, Errors: {len(errs)}")

if TG and TGCID:
    msg = f"🔧 *FIX Below-Floor Raymundo*\n\n"
    msg += f"Items debajo de floor: *{len(below)}*\n"
    msg += f"Subidos: *{len(fixed)}*\n"
    msg += f"Errores: *{len(errs)}*\n\n"
    if fixed:
        msg += "*Ajustados:*\n"
        for f in fixed[:10]:
            msg += f"• `{f['iid']}` {f['model']} ${f['cur']}→${f['floor']}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
