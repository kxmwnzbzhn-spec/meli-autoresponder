#!/usr/bin/env python3
"""Busca TODOS los catalog_product_ids de JBL Clip 5 disponibles en MELI MX
para identificar cuáles aún no estamos publicando.
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "refresh_token": RT,
})
at = r.json()["access_token"]
H = {"Authorization": f"Bearer {at}"}

# Cargar catálogos ya publicados
with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)
already_pub_cpids = set()
for iid, meta in cfg.items():
    cpid = meta.get("catalog_product_id")
    if cpid:
        already_pub_cpids.add(cpid)
print(f"Ya publicados en Raymundo: {already_pub_cpids}\n")

# 1) Buscar catalog products via /products/search
print("=== Búsqueda 1: /products/search?q=JBL Clip 5 ===")
found_catalogs = {}  # cpid → details
for q in ["JBL Clip 5", "Clip 5 JBL", "JBL Audio Clip 5", "parlante jbl clip 5", "bocina jbl clip 5"]:
    print(f"\n  query: '{q}'")
    try:
        r = requests.get(
            "https://api.mercadolibre.com/products/search",
            headers=H,
            params={"status": "active", "site_id": "MLM", "q": q, "limit": 50},
            timeout=20,
        )
        if r.status_code == 200:
            d = r.json()
            results = d.get("results", [])
            print(f"    {len(results)} resultados")
            for p in results:
                pid = p.get("id")
                if pid and pid.startswith("MLM") and not pid.startswith("MLMU"):
                    name = (p.get("name") or "")[:80]
                    if "clip 5" in name.lower() or "clip5" in name.lower():
                        found_catalogs[pid] = {
                            "name": name,
                            "site_id": p.get("site_id"),
                            "domain_id": p.get("domain_id"),
                            "buy_box_winner": p.get("buy_box_winner"),
                        }
        else:
            print(f"    err {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"    exception: {e}")
    time.sleep(1)

# 2) Búsqueda alternativa via /sites/MLM/search filter category bocinas
print("\n=== Búsqueda 2: /sites/MLM/search por keywords + category MLM59800 ===")
for q in ["JBL Clip 5", "Clip 5"]:
    try:
        r = requests.get(
            "https://api.mercadolibre.com/sites/MLM/search",
            params={"q": q, "category": "MLM59800", "limit": 50,
                    "official_store": "all", "buying_mode": "buy_it_now"},
            timeout=20,
        )
        if r.status_code == 200:
            d = r.json()
            for it in d.get("results", []):
                cpid = it.get("catalog_product_id")
                if cpid and cpid not in found_catalogs:
                    name = (it.get("title") or "")[:80]
                    if "clip 5" in name.lower() or "clip5" in name.lower():
                        found_catalogs[cpid] = {
                            "name": name,
                            "from_item_search": True,
                        }
        time.sleep(1)
    except Exception as e:
        print(f"  err: {e}")

# Reporte
print(f"\n{'=' * 70}")
print(f"Total catálogos Clip 5 detectados: {len(found_catalogs)}")
print(f"Ya publicados:                    {len(already_pub_cpids)}")

new_catalogs = []
already = []
for cpid, info in sorted(found_catalogs.items()):
    if cpid in already_pub_cpids:
        already.append((cpid, info))
    else:
        new_catalogs.append((cpid, info))

print(f"\n✅ YA PUBLICADOS ({len(already)}):")
for cpid, info in already:
    print(f"  {cpid}: {info.get('name','?')}")

print(f"\n🆕 NUEVOS (sin publicar): {len(new_catalogs)}")
for cpid, info in new_catalogs:
    print(f"  {cpid}: {info.get('name','?')}")

# TG resumen
if TG and TGCID:
    msg = f"🔍 *Catálogos JBL Clip 5 disponibles en MELI*\n\n"
    msg += f"Total detectados: *{len(found_catalogs)}*\n"
    msg += f"Ya publicados: {len(already)}\n"
    msg += f"🆕 *Nuevos sin publicar: {len(new_catalogs)}*\n\n"
    if new_catalogs:
        msg += "Catálogos disponibles para sumar al ataque:\n"
        for cpid, info in new_catalogs[:20]:
            name = info.get('name', '?')[:50]
            msg += f"• `{cpid}`: {name}\n"
        if len(new_catalogs) > 20:
            msg += f"... y {len(new_catalogs)-20} más\n"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
        timeout=20,
    )

# Save report
with open("clip5_catalogs_audit.json", "w") as f:
    json.dump({
        "total_found": len(found_catalogs),
        "already_published": [{"cpid": c, **i} for c, i in already],
        "new_to_publish":   [{"cpid": c, **i} for c, i in new_catalogs],
    }, f, indent=2, ensure_ascii=False)
print(f"\n📋 Reporte guardado: clip5_catalogs_audit.json")
