#!/usr/bin/env python3
"""Publica TODOS los catálogos Go 4 / Go 3 Negro limpios en Raymundo a $999.

- Lee go4_go3_audit.json para obtener clean list
- Filtra:
   1. ya publicados (catalog_product_id en stock_config_raymundo)
   2. colores sin stock (verde, blanco, morado, None)
- Publica los restantes
- Reparte stock pool por color across all pubs
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

PRICE = 999.0
VISIBLE_QTY = 1
CATEGORY = "MLM59800"

# Stock pools por color/modelo
POOL_SIZE = {
    ("Go 4", "Negro"):       130,
    ("Go 4", "Azul"):        480,
    ("Go 4", "Rojo"):        407,
    ("Go 4", "Aqua"):       1013,
    ("Go 4", "Azul Marino"): 466,
    ("Go 4", "Camuflaje"):   549,
    ("Go 4", "Rosa"):        129,
    ("Go 3", "Negro"):       936,
}
COLORS_WITH_STOCK = set(POOL_SIZE.keys())

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID, "client_secret": APP_SECRET, "refresh_token": RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}",
     "Content-Type": "application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

# Cargar audit y config
with open("go4_go3_audit.json") as f:
    audit = json.load(f)
clean_list = audit.get("to_publish", [])
print(f"Audit: {len(clean_list)} clean candidates\n")

with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)
already_pub_cpids = {meta.get("catalog_product_id") for meta in cfg.values() if meta.get("catalog_product_id")}
print(f"Ya publicados: {len(already_pub_cpids)} catálogos\n")

# Filtrar
to_publish = []
skipped_no_stock = []
skipped_already = []
for r in clean_list:
    cpid = r["cpid"]
    color = r.get("title_color")
    model = r["model_target"]
    key = (model, color)
    if key not in COLORS_WITH_STOCK:
        skipped_no_stock.append(r)
        continue
    if cpid in already_pub_cpids:
        skipped_already.append(r)
        continue
    to_publish.append(r)

print(f"📤 Publicar:           {len(to_publish)}")
print(f"⏭️  Skip sin stock:    {len(skipped_no_stock)}")
print(f"⏭️  Skip ya publicados: {len(skipped_already)}\n")

# Publicar
results = []
for r in to_publish:
    cpid = r["cpid"]
    color = r["title_color"]
    model = r["model_target"]
    print(f"=== {model} {color}: {cpid} ===")

    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H).json()
    title = (p.get("name") or f"JBL {model} {color}")[:60]
    print(f"  title: '{title}'")

    payload = {
        "title": title,
        "category_id": CATEGORY,
        "catalog_product_id": cpid,
        "catalog_listing": True,
        "price": PRICE,
        "available_quantity": VISIBLE_QTY,
        "currency_id": "MXN",
        "condition": "new",
        "listing_type_id": "gold_special",
        "sale_terms": [
            {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
            {"id": "WARRANTY_TIME", "value_name": "30 días"}
        ],
        "shipping": {"mode": "me2", "free_shipping": False, "tags": ["self_service_in"]}
    }
    pr = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
    print(f"  POST → {pr.status_code}")
    try:
        j = pr.json()
        if pr.status_code in (200, 201):
            iid = j.get("id")
            print(f"  ✅ {iid}")
            cfg[iid] = {
                "label": f"{model} {color}",
                "real_stock": 0,  # se asigna abajo en reparto
                "min_visible": VISIBLE_QTY,
                "auto_replenish": True,
                "replenish_quantity": VISIBLE_QTY,
                "catalog_war": True,
                "floor_price": 199 if model == "Go 4" else 99,
                "ceiling_price": 1499,
                "color": color,
                "model": model,
                "catalog_product_id": cpid,
            }
            results.append({"cpid": cpid, "model": model, "color": color,
                            "item_id": iid, "permalink": j.get("permalink")})
        else:
            err = j.get("message", str(j))[:200]
            print(f"  ❌ {err}")
            results.append({"cpid": cpid, "model": model, "color": color, "error": err})
    except Exception as e:
        print(f"  raw err: {e}")
        results.append({"cpid": cpid, "model": model, "color": color, "error": str(e)})
    time.sleep(2)

# Reparto stock por color
print("\n" + "=" * 60)
print("REPARTO STOCK POR POOL:")
pubs_by_pool = {}
for iid, meta in cfg.items():
    model = meta.get("model")
    color = meta.get("color")
    if (model, color) in POOL_SIZE:
        pubs_by_pool.setdefault((model, color), []).append(iid)

for key, total in POOL_SIZE.items():
    pubs = pubs_by_pool.get(key, [])
    if not pubs:
        continue
    n = len(pubs)
    per = total // n
    rem = total - per * n
    print(f"\n  {key[0]} {key[1]}: pool {total}u / {n} pubs = {per}u c/u (resto {rem})")
    for i, iid in enumerate(pubs):
        amt = per + (rem if i == 0 else 0)
        cfg[iid]["real_stock"] = amt - VISIBLE_QTY
        cfg[iid]["pool_total"] = total
    print(f"    pubs: {pubs[:5]}{'...' if len(pubs) > 5 else ''}")

with open("stock_config_raymundo.json", "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

ok = [r for r in results if "item_id" in r]
fail = [r for r in results if "error" in r]
print(f"\n✅ Publicados: {len(ok)}/{len(to_publish)}")
print(f"❌ Errores:    {len(fail)}")

# Total nuevo en raymundo
total_clip5_g4_g3 = sum(1 for v in cfg.values()
                        if v.get("model") in ("Clip 5", "Go 4", "Go 3"))
print(f"\nTotal Clip5+Go4+Go3 en Raymundo: {total_clip5_g4_g3}")

# Telegram
if TG and TGCID:
    msg = f"🚀 *Batch Go 4 + Go 3 — Raymundo*\n\n"
    msg += f"✅ Publicados: *{len(ok)}*/{len(to_publish)}\n"
    if fail:
        msg += f"❌ Errores: {len(fail)}\n"
    msg += f"⏭️ Sin stock: {len(skipped_no_stock)}\n"
    msg += f"⏭️ Ya publicados: {len(skipped_already)}\n\n"
    msg += "*Distribución pool:*\n"
    for (model, color), total in POOL_SIZE.items():
        n = len(pubs_by_pool.get((model, color), []))
        if n:
            msg += f"• {model} {color}: {total}u / {n} pubs ({total // n}u c/u)\n"
    msg += f"\n📊 Total Clip5+Go4+Go3 en Raymundo: *{total_clip5_g4_g3}*\n"
    msg += "⚔️ Catalog war activo, gap \\$250 vs FULL"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
        timeout=20,
    )
