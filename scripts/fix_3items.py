"""1) Subir floor a $599 + setear precio safer para los 2 items con precio bajo
   2) Verificar si MLM46039390 ya está publicado en Raymundo (Go 3 Negro)"""
import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me['id']
print(f"Cuenta: {me['nickname']} ({uid})")

# === 1) Fix los 2 items con precio bajo: subir a $599 (floor decente) ===
TO_FIX = [
    ("MLM2891189883", "Go 4", "Azul"),
    ("MLM5246052014", "Go 4", "Rojo"),
]
NEW_PRICE = 599

with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)

for iid, model, color in TO_FIX:
    print(f"\n=== Fix {iid} ({model} {color}) ===")
    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"price": NEW_PRICE})
    print(f"  PUT price=${NEW_PRICE} → {pr.status_code}")
    if pr.status_code >= 400:
        print(f"    err: {pr.text[:300]}")
    # Patchar config
    if iid not in cfg:
        cfg[iid] = {}
    cfg[iid].update({
        "label": f"{model} {color}",
        "model": model,
        "color": color,
        "floor_price": 599,
        "ceiling_price": 1499,
        "catalog_war": True,
        "auto_replenish": True,
        "min_visible": 1,
        "replenish_quantity": 1,
    })
    print(f"  config patched: floor=$599")

# === 2) Verificar MLM46039390 (Go 3 Negro "Jbl Go3 Black Negro") ===
TARGET_CPID = "MLM46039390"
print(f"\n\n=== Buscar catalog {TARGET_CPID} en config ===")
exists_iid = None
for iid, meta in cfg.items():
    if meta.get("catalog_product_id") == TARGET_CPID:
        exists_iid = iid
        break
if exists_iid:
    print(f"  ✅ YA publicado: {exists_iid}")
    # Get item info
    it = requests.get(f"https://api.mercadolibre.com/items/{exists_iid}", headers=H, timeout=10).json()
    print(f"  title: {it.get('title','?')[:80]}")
    print(f"  price: ${it.get('price')}")
    print(f"  status: {it.get('status')}")
    print(f"  link: {it.get('permalink','?')}")
else:
    print(f"  ⚠️ NO publicado, creándolo ahora")
    p = requests.get(f"https://api.mercadolibre.com/products/{TARGET_CPID}", headers=H, timeout=15).json()
    title = (p.get("name") or "JBL Go 3 Negro")[:60]
    payload = {
        "title": title,
        "category_id": "MLM59800",
        "catalog_product_id": TARGET_CPID,
        "catalog_listing": True,
        "price": 999,
        "available_quantity": 1,
        "currency_id": "MXN",
        "condition": "new",
        "listing_type_id": "gold_special",
        "sale_terms": [
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
        "shipping": {"mode":"me2","free_shipping":False,"tags":["self_service_in"]},
    }
    pr = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
    j = pr.json()
    print(f"  POST → {pr.status_code}")
    if pr.status_code in (200,201):
        new_iid = j.get("id")
        print(f"  ✅ {new_iid}: {j.get('permalink')}")
        cfg[new_iid] = {
            "label": "Go 3 Negro",
            "model": "Go 3", "color": "Negro",
            "real_stock": 50, "min_visible": 1,
            "auto_replenish": True, "replenish_quantity": 1,
            "catalog_war": True,
            "floor_price": 99, "ceiling_price": 1499,
            "catalog_product_id": TARGET_CPID,
        }
    else:
        print(f"  ❌ {j}")

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

if TG and TGCID:
    msg = f"🔧 *Fix Raymundo*\n\n"
    msg += f"✅ Subí precio MLM2891189883 → \\$599\n"
    msg += f"✅ Subí precio MLM5246052014 → \\$599\n"
    msg += f"   (floor era 0, bot bajaba a \\$370-388 sin sentido)\n\n"
    msg += f"🔍 MLM46039390 Go 3 Negro: "
    msg += "ya publicado" if exists_iid else "publicado ahora"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg}, timeout=20)
