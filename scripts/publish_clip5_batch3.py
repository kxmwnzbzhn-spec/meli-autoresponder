#!/usr/bin/env python3
"""Publica 21 catálogos Clip 5 validados en Raymundo a $999.
Reparte el stock total por color entre TODAS las publicaciones del mismo pool físico.
"""
import os, requests, json, time, math

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

PRICE = 999.0
VISIBLE_QTY = 1
CATEGORY = "MLM59800"

# 21 catálogos limpios (descartados los 4 con conflicto)
NEW_CATALOGS = [
    # (cpid, color_pool)
    ("MLM43541894", "Negro"),
    ("MLM44963647", "Negro"),
    ("MLM57996147", "Negro"),
    ("MLM58837986", "Negro"),
    ("MLM42622714", "Negro"),
    ("MLM44713950", "Negro"),
    ("MLM54533831", "Negro"),
    ("MLM61814218", "Negro"),
    ("MLM40329314", "Azul"),
    ("MLM58592190", "Azul"),
    ("MLM61825899", "Azul"),
    ("MLM44573520", "Morado"),
    ("MLM44712007", "Morado"),
    ("MLM49054893", "Morado"),
    ("MLM45586155", "Morado"),
    ("MLM47145951", "Morado"),
    ("MLM44712057", "Camuflaje"),
    ("MLM44714337", "Rosa"),
    ("MLM63875183", "Rosa"),
    ("MLM64288232", "Rosa"),
    ("MLM44465821", "Mixto"),  # genérico
]

# Pool físico total por color
POOL_SIZE = {
    "Negro":     246,
    "Rojo":      164,
    "Azul":      480,
    "Morado":    256,
    "Camuflaje": 240,
    "Rosa":      204,
    "Mixto":      40,
}

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "refresh_token": RT,
})
at = r.json()["access_token"]
H = {"Authorization": f"Bearer {at}", "Content-Type": "application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

# Cargar config
config_file = "stock_config_raymundo.json"
with open(config_file) as f:
    cfg = json.load(f)

# Detectar publicaciones existentes Clip 5 por color para redistribuir
existing_clip5_by_color = {}  # color → [iid, ...]
for iid, meta in cfg.items():
    if "Clip 5" not in str(meta.get("label", "")):
        continue
    color = meta.get("color")
    if color in ("Camuflaje", "Negro", "Rojo", "Azul", "Morado", "Rosa", "Mixto"):
        existing_clip5_by_color.setdefault(color, []).append(iid)

print("Existing Clip 5 pubs por color:")
for c, lst in existing_clip5_by_color.items():
    print(f"  {c}: {len(lst)} pubs")
print()

# === PUBLICAR LOS 21 NUEVOS ===
results = []
for cpid, color in NEW_CATALOGS:
    print(f"=== {color}: {cpid} ===")

    # Verificar no duplicado
    already = any(meta.get("catalog_product_id") == cpid for meta in cfg.values())
    if already:
        print(f"  ⏭️ ya existe, skip")
        results.append({"cpid": cpid, "color": color, "skipped": "duplicate"})
        continue

    # Get catalog product info
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H).json()
    title = (p.get("name") or f"JBL Clip 5 {color}")[:60]
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
            print(f"  ✅ {iid} | ${j.get('price')}")
            cfg[iid] = {
                "label": f"Clip 5 {color}",
                "real_stock": 0,  # se asignará después en el reparto
                "min_visible": VISIBLE_QTY,
                "auto_replenish": True,
                "replenish_quantity": VISIBLE_QTY,
                "catalog_war": True,
                "floor_price": 799,
                "ceiling_price": 1499,
                "color": color,
                "model": "Clip 5",
                "catalog_product_id": cpid,
                "shared_pool": color,
            }
            existing_clip5_by_color.setdefault(color, []).append(iid)
            results.append({"cpid": cpid, "color": color, "item_id": iid, "permalink": j.get("permalink")})
        else:
            err = j.get("message", str(j))[:300]
            print(f"  ❌ {err}")
            results.append({"cpid": cpid, "color": color, "error": err})
    except Exception as e:
        print(f"  raw err: {e}")
        results.append({"cpid": cpid, "color": color, "error": str(e)})

    time.sleep(2)

# === REPARTIR STOCK POR COLOR ===
print("\n" + "=" * 60)
print("REPARTO DE STOCK POR POOL:")
for color, total in POOL_SIZE.items():
    pubs = existing_clip5_by_color.get(color, [])
    if not pubs:
        continue
    n = len(pubs)
    per_pub = total // n
    remainder = total - per_pub * n
    print(f"\n  {color}: pool {total}u / {n} pubs = {per_pub}u c/u (resto {remainder})")
    for i, iid in enumerate(pubs):
        # Primer pub recibe el remainder
        amt = per_pub + (remainder if i == 0 else 0)
        cfg[iid]["real_stock"] = amt - VISIBLE_QTY  # restar lo visible
        cfg[iid]["shared_pool"] = color
        cfg[iid]["pool_total"] = total
        print(f"    {iid}: {amt}u (real_stock={amt - VISIBLE_QTY})")

with open(config_file, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

# === Resumen ===
ok = [r for r in results if "item_id" in r]
sk = [r for r in results if "skipped" in r]
fail = [r for r in results if "error" in r]
print(f"\n✅ Publicados: {len(ok)}")
print(f"⏭️ Skipped:    {len(sk)}")
print(f"❌ Errores:    {len(fail)}")

# Total Clip 5 ahora en raymundo
total_clip5 = sum(1 for v in cfg.values() if "Clip 5" in str(v.get("label", "")))
print(f"\nTotal Clip 5 publicaciones en Raymundo: {total_clip5}")

# Telegram
if TG and TGCID:
    msg = f"🚀 *Batch 3 Clip 5 — Raymundo*\n\n"
    msg += f"✅ Publicados: *{len(ok)}*/21\n"
    if fail:
        msg += f"❌ Errores: {len(fail)}\n"
    if sk:
        msg += f"⏭️ Skip dups: {len(sk)}\n"
    msg += f"\n📊 *Total Clip 5 activos:* {total_clip5}\n\n"
    msg += "*Distribución pool:*\n"
    for color, total in POOL_SIZE.items():
        pubs = existing_clip5_by_color.get(color, [])
        if pubs:
            per = total // len(pubs)
            msg += f"• {color}: {total}u / {len(pubs)} pubs ({per}u c/u)\n"
    msg += f"\n⚔️ Catalog war activo, gap \\$250 vs FULL"
    if fail:
        msg += "\n\n_Errores:_\n"
        for r in fail[:5]:
            msg += f"• `{r['cpid']}`: {r['error'][:80]}\n"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
        timeout=20,
    )
