#!/usr/bin/env python3
"""
RAYMUNDO ONLY CATALOG
=====================
Deja activos SOLO los items con catalog_listing=true.
Pausa todas las publicaciones tradicionales (catalog_listing=false).
Marca paused_by_user=True en stock_config_raymundo.json para que
el bot de auto-replenish/reactivate NO las reactive.
"""
import os, requests, json, time

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

r = requests.post(
    "https://api.mercadolibre.com/oauth/token",
    data={"grant_type": "refresh_token", "client_id": APP_ID,
          "client_secret": APP_SECRET, "refresh_token": RT},
    timeout=20,
).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type": "application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

all_ids = set()
for st in ("active", "paused"):
    offset = 0
    while True:
        rr = requests.get(
            f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}",
            headers=H, timeout=15,
        ).json()
        b = rr.get("results", [])
        if not b:
            break
        all_ids.update(b)
        offset += 50
        if offset >= rr.get("paging", {}).get("total", 0):
            break

print(f"Total items Raymundo: {len(all_ids)}\n")

try:
    cfg = json.load(open("stock_config_raymundo.json"))
except FileNotFoundError:
    cfg = {}

paused_traditional = []
kept_catalog = []
already_paused_traditional = []
errors = []

batch = list(all_ids)
items_data = {}
for i in range(0, len(batch), 20):
    chunk = ",".join(batch[i:i+20])
    rr = requests.get(
        f"https://api.mercadolibre.com/items?ids={chunk}&attributes=id,title,status,catalog_listing,available_quantity,price",
        headers=H, timeout=20,
    ).json()
    for it in rr:
        if it.get("code") == 200:
            b = it["body"]
            items_data[b["id"]] = b

print(f"Items con metadata: {len(items_data)}\n")

for iid, b in items_data.items():
    title = (b.get("title") or "")[:55]
    status = b.get("status")
    is_catalog = b.get("catalog_listing", False)

    if is_catalog:
        kept_catalog.append(iid)
        if iid in cfg:
            cfg[iid]["active"] = True
            cfg[iid]["auto_replenish"] = True
            if "paused_by_user" in cfg[iid]:
                del cfg[iid]["paused_by_user"]
        print(f"  CATALOG   {iid} ({status:6s}) | '{title}'")
        continue

    if status == "paused":
        already_paused_traditional.append(iid)
        if iid in cfg:
            cfg[iid]["active"] = False
            cfg[iid]["paused_by_user"] = True
        print(f"  ALREADY-PAUSED-TRAD {iid} | '{title}'")
        continue

    rp = requests.put(
        f"https://api.mercadolibre.com/items/{iid}",
        headers=H, json={"status": "paused"}, timeout=15,
    )
    if rp.status_code == 200:
        paused_traditional.append(iid)
        if iid in cfg:
            cfg[iid]["active"] = False
            cfg[iid]["paused_by_user"] = True
        else:
            cfg[iid] = {
                "line": "Tradicional-Raymundo-Pausada",
                "label": title,
                "active": False,
                "paused_by_user": True,
                "auto_replenish": False,
            }
        print(f"  PAUSED-TRAD {iid} | '{title}'")
    else:
        errors.append((iid, rp.status_code, rp.text[:100]))
        print(f"  ERROR {iid}: {rp.status_code} {rp.text[:80]}")
    time.sleep(0.15)

with open("stock_config_raymundo.json", "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 60)
print(f"Catalogos activos (preservados): {len(kept_catalog)}")
print(f"Tradicionales pausadas ahora:    {len(paused_traditional)}")
print(f"Tradicionales ya pausadas:       {len(already_paused_traditional)}")
print(f"Errores: {len(errors)}")
print("=" * 60)
