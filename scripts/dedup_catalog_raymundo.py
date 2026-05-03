#!/usr/bin/env python3
"""DEDUP catalog Raymundo: si hay >1 item activo apuntando al MISMO catalog_product_id,
mantener el MEJOR (mas ventas, luego mas viejo) y CERRAR los demas para evitar
canibalizacion.

Criterio winner por catalog_product_id:
1. mayor sold_quantity
2. mas viejo (date_created mas temprano)
3. precio mas alto (mejor margen)
"""
import os, requests, time
from collections import defaultdict

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me["id"]
print(f"Cuenta {me['nickname']} ({uid}) | DRY_RUN={DRY_RUN}\n")

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
                       "attributes":"id,title,price,catalog_listing,catalog_product_id,sold_quantity,date_created,status"},
                     timeout=20).json()
    for resp in r:
        if resp.get("code") == 200:
            items.append(resp.get("body"))
    time.sleep(0.15)

# Agrupar por catalog_product_id
groups = defaultdict(list)
for it in items:
    if it.get("status") != "active": continue
    if not it.get("catalog_listing"): continue
    cpid = it.get("catalog_product_id")
    if not cpid: continue
    groups[cpid].append(it)

dups = {cpid: lst for cpid, lst in groups.items() if len(lst) > 1}
print(f"Catalog product_ids con duplicados: {len(dups)}")

closed = []
kept = []
errors = []

for cpid, lst in dups.items():
    # Ordenar para encontrar el winner
    # 1. mayor sold_quantity
    # 2. mas viejo (date_created)
    # 3. mayor precio
    sorted_items = sorted(
        lst,
        key=lambda x: (
            -int(x.get("sold_quantity") or 0),
            x.get("date_created") or "9999",
            -float(x.get("price") or 0),
        )
    )
    winner = sorted_items[0]
    losers = sorted_items[1:]

    print(f"\n--- cpid {cpid} ({len(lst)} items) ---")
    print(f"  👑 KEEP: {winner['id']} sold={winner.get('sold_quantity')} ${winner.get('price')} {winner.get('title','')[:50]}")
    kept.append({
        "iid": winner["id"], "cpid": cpid,
        "sold": winner.get("sold_quantity"),
        "price": winner.get("price"),
        "title": winner.get("title","")[:60]
    })

    for L in losers:
        print(f"  ⛔ CLOSE: {L['id']} sold={L.get('sold_quantity')} ${L.get('price')} {L.get('title','')[:50]}")
        if not DRY_RUN:
            pr = requests.put(f"https://api.mercadolibre.com/items/{L['id']}",
                              headers=H, json={"status":"closed"})
            if pr.status_code == 200:
                closed.append({
                    "iid": L["id"], "cpid": cpid,
                    "sold": L.get("sold_quantity"),
                    "price": L.get("price"),
                    "title": L.get("title","")[:60]
                })
            else:
                errors.append({"iid": L["id"], "err": pr.text[:120]})
                print(f"     ❌ {pr.status_code} {pr.text[:100]}")
        time.sleep(0.2)

print(f"\n{'='*60}\n=== RESUMEN ===")
print(f"Total catalog items active: {sum(len(v) for v in groups.values())}")
print(f"Catálogos únicos: {len(groups)}")
print(f"Catálogos con duplicados: {len(dups)}")
print(f"Items conservados (winners): {len(kept)}")
print(f"Items CERRADOS: {len(closed)}")
print(f"Errores: {len(errors)}")

if TG and TGCID:
    msg = f"🧹 *DEDUP Catalog Raymundo*\n\n"
    msg += f"📋 Catálogos con dups: *{len(dups)}*\n"
    msg += f"⛔ Items cerrados: *{len(closed)}*\n"
    msg += f"👑 Winners conservados: *{len(kept)}*\n"
    if errors: msg += f"❌ Errores: *{len(errors)}*\n"
    if closed:
        msg += "\n*Cerradas:*\n"
        for c in closed[:15]:
            msg += f"• `{c['iid']}` ${c['price']} sold={c['sold']}\n"
        if len(closed) > 15:
            msg += f"_...y {len(closed)-15} más_\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
