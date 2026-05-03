#!/usr/bin/env python3
"""Publica 5 catálogos Clip 5 adicionales en Raymundo a $999.
- Resuelve user_product → catalog_product_id (para URLs con /up/MLMU...)
- Verifica contra stock_config_raymundo.json para no duplicar lo ya publicado
- Mismas reglas: 1 visible, auto-replenish, catalog war floor 799/ceiling 1499
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

# IDs from URLs the user provided (in order)
INPUTS = [
    # (id_from_url, friendly_label, color_guess)
    ("MLM46022592",     "Clip 5 Rojo (cover)",     "Rojo"),
    ("MLMU3914306586",  "Clip 5 Camuflada",        "Camuflaje"),
    ("MLMU3782725835",  "Clip 5 (sin color)",      "Mixto"),
    ("MLMU3814174756",  "Clip 5 Rojo (otro user)", "Rojo"),
    ("MLM46042650",     "Clip 5 Negro 7W",         "Negro"),
]

PRICE = 999.0
VISIBLE_QTY = 1
CATEGORY = "MLM59800"

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

# Cargar stock_config_raymundo para detectar duplicados
config_file = "stock_config_raymundo.json"
try:
    with open(config_file) as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

# Set de catalogos ya publicados
already_published_cpids = set()
for iid, meta in cfg.items():
    cpid = meta.get("catalog_product_id")
    if cpid:
        already_published_cpids.add(cpid)
print(f"📋 Catálogos ya en stock_config: {already_published_cpids}\n")

def resolve_to_catalog(input_id):
    """Resuelve un id (catalog o user_product) al catalog_product_id real."""
    # Si empieza con MLMU es user_product, hay que buscar el catalogo asociado
    if input_id.startswith("MLMU"):
        # Endpoint: GET /user-products/{id}
        r = requests.get(f"https://api.mercadolibre.com/user-products/{input_id}", headers=H)
        if r.status_code == 200:
            d = r.json()
            cpid = d.get("catalog_product_id") or d.get("parent_id")
            return cpid, d
        # Alt: a veces /products/MLMU... también funciona
        r = requests.get(f"https://api.mercadolibre.com/products/{input_id}", headers=H)
        if r.status_code == 200:
            d = r.json()
            cpid = d.get("catalog_product_id") or d.get("id")
            return cpid, d
        return None, {"error": r.status_code, "text": r.text[:200]}
    # Si empieza con MLM (sin U) es catalog directo
    return input_id, None

results = []
for input_id, label, color in INPUTS:
    print(f"=== {label} (input: {input_id}) ===")

    cpid, info = resolve_to_catalog(input_id)
    if not cpid:
        print(f"  ❌ No pude resolver a catalog: {info}")
        results.append({"input": input_id, "label": label, "error": "no_catalog_resolved"})
        continue
    print(f"  → catalog_product_id: {cpid}")

    if cpid in already_published_cpids:
        print(f"  ⏭️  ya publicado, SKIP")
        results.append({"input": input_id, "label": label, "cpid": cpid, "skipped": "already_published"})
        continue

    # Get product info
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H).json()
    title = (p.get("name") or label)[:60]
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
            print(f"  ✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
            print(f"     {j.get('permalink', '')}")
            cfg[iid] = {
                "label": label,
                "real_stock": 100,  # placeholder; user actualizará
                "min_visible": VISIBLE_QTY,
                "auto_replenish": True,
                "replenish_quantity": VISIBLE_QTY,
                "catalog_war": True,
                "floor_price": 799,
                "ceiling_price": 1499,
                "color": color,
                "model": "Clip 5",
                "catalog_product_id": cpid,
            }
            already_published_cpids.add(cpid)
            results.append({"input": input_id, "label": label, "cpid": cpid,
                            "item_id": iid, "permalink": j.get("permalink"),
                            "price": j.get("price")})
        else:
            err = j.get("message", str(j))[:300]
            print(f"  ❌ {err}")
            results.append({"input": input_id, "label": label, "cpid": cpid, "error": err})
    except Exception as e:
        print(f"  raw: {pr.text[:600]} err={e}")
        results.append({"input": input_id, "label": label, "cpid": cpid, "error": str(e)})

    time.sleep(2)

# Save updated config
with open(config_file, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 60)
print("RESULTS:")
for r in results:
    print(f"  {json.dumps(r, ensure_ascii=False)}")

# Telegram
if TG and TGCID:
    ok = [r for r in results if "item_id" in r]
    skipped = [r for r in results if "skipped" in r]
    failed = [r for r in results if "error" in r]
    msg = f"📦 *Clip 5 batch v2 — Raymundo*\n\n"
    if ok:
        msg += f"✅ *Publicados:* {len(ok)}\n"
        for r in ok:
            msg += f"• {r['label']}: `{r['item_id']}` ({r['cpid']})\n"
    if skipped:
        msg += f"\n⏭️ *Ya existían:* {len(skipped)}\n"
        for r in skipped:
            msg += f"• {r['label']}: {r['cpid']}\n"
    if failed:
        msg += f"\n❌ *Errores:* {len(failed)}\n"
        for r in failed:
            msg += f"• {r['label']}: {r.get('error','?')[:80]}\n"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg},
        timeout=20,
    )
