#!/usr/bin/env python3
"""Publica 5 catálogos Clip 5 en Raymundo a $999.
Después se enrollan al catalog_war y al auto-replenish.
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

CATALOGS = [
    ("MLM44714111", "Morado",    256),
    ("MLM37361046", "Rojo",      164),
    ("MLM37110181", "Negro",     246),
    ("MLM37110751", "Azul",      480),
    ("MLM44714150", "Camuflaje",  40),  # placeholder - confirmar
]
PRICE = 999.0
VISIBLE_QTY = 1   # solo 1 a la vista, master_stock con auto-replenish maneja el resto
CATEGORY = "MLM59800"  # Bocinas Bluetooth

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

# Cargar config existente Raymundo
config_file = "stock_config_raymundo.json"
try:
    with open(config_file) as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

results = []

for cpid, color, real_stock in CATALOGS:
    print(f"=== Clip 5 {color} (catalogo {cpid}) ===")

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

    r = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
    print(f"  POST → {r.status_code}")
    try:
        j = r.json()
        if r.status_code in (200, 201):
            iid = j.get("id")
            print(f"  ✅ {iid} | ${j.get('price')} | qty={j.get('available_quantity')}")
            print(f"     {j.get('permalink', '')}")
            # Agregar a stock_config_raymundo
            cfg[iid] = {
                "label": f"Clip 5 {color}",
                "real_stock": real_stock - VISIBLE_QTY,
                "min_visible": VISIBLE_QTY,
                "auto_replenish": True,
                "replenish_quantity": VISIBLE_QTY,
                "catalog_war": True,
                "floor_price": 799,  # piso de catalog war
                "ceiling_price": 1499,
                "color": color,
                "model": "Clip 5",
                "catalog_product_id": cpid,
            }
            results.append({"color": color, "item_id": iid, "permalink": j.get("permalink"),
                            "price": j.get("price"), "real_stock": real_stock})
        else:
            print(f"  ❌ {json.dumps(j, ensure_ascii=False)[:800]}")
            results.append({"color": color, "error": j.get("message", str(j))[:200]})
    except Exception as e:
        print(f"  raw: {r.text[:600]} err={e}")
        results.append({"color": color, "error": str(e)[:200]})
    time.sleep(2)

# Guardar stock_config_raymundo actualizado
with open(config_file, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 60)
print("RESULTS:")
for r in results:
    print(f"  {json.dumps(r, ensure_ascii=False)}")
print(f"\nstock_config_raymundo.json actualizado con {len(cfg)} items totales")

# Telegram
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CID = os.environ.get("TELEGRAM_CHAT_ID", "")
if TG and CID:
    ok = [r for r in results if "item_id" in r]
    fail = [r for r in results if "error" in r]
    msg = f"📦 *Publicación Clip 5 en Raymundo*\n\n"
    msg += f"✅ {len(ok)}/{len(results)} catálogos publicados a ${PRICE:.0f}\n\n"
    for r in ok:
        msg += f"• Clip 5 {r['color']}: `{r['item_id']}` ({r['real_stock']}u stock)\n"
    if fail:
        msg += f"\n❌ Errores:\n"
        for r in fail:
            msg += f"• {r['color']}: {r['error']}\n"
    msg += f"\nTodos en catalog war (floor $799, ceiling $1499)\n1 visible + master_stock auto-replenish."
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": CID, "parse_mode": "Markdown", "text": msg},
        timeout=20,
    )
