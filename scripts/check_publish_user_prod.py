import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

USER_PROD_ID = "MLMU3662152430"

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}

# Resolver user_product → catalog_product_id
r = requests.get(f"https://api.mercadolibre.com/user-products/{USER_PROD_ID}", headers=H, timeout=20)
print(f"user-products fetch: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    cpid = d.get("catalog_product_id") or d.get("parent_id")
    print(f"  catalog_product_id: {cpid}")
else:
    # alt: direct products endpoint
    r2 = requests.get(f"https://api.mercadolibre.com/products/{USER_PROD_ID}", headers=H, timeout=20)
    print(f"products fetch: {r2.status_code}")
    if r2.status_code == 200:
        d = r2.json()
        cpid = d.get("catalog_product_id") or d.get("id")
        print(f"  resolved: {cpid}")
    else:
        cpid = None
        print(f"  err: {r2.text[:200]}")

if not cpid:
    print("ABORT: no catalog resolved")
    raise SystemExit(0)

# Verificar si ya tenemos
with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)
exists = None
for iid, meta in cfg.items():
    if meta.get("catalog_product_id") == cpid:
        exists = iid; break
if exists:
    print(f"\n✅ YA publicado: {exists}")
    it = requests.get(f"https://api.mercadolibre.com/items/{exists}", headers=H, timeout=10).json()
    print(f"  title: {it.get('title','?')[:80]}")
    print(f"  price: ${it.get('price')}")
    print(f"  link: {it.get('permalink')}")
    if TG and TGCID:
        requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
            "chat_id":TGCID,"parse_mode":"Markdown",
            "text":f"✅ Catálogo `{cpid}` (Go 3 Negro) ya publicado en Raymundo: `{exists}`"}, timeout=20)
else:
    print(f"\n📤 Publicando catálogo {cpid}...")
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=15).json()
    title = (p.get("name") or "JBL Go 3 Negro")[:60]
    payload = {
        "title": title,
        "category_id": "MLM59800",
        "catalog_product_id": cpid,
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
            "label":"Go 3 Negro","model":"Go 3","color":"Negro",
            "real_stock": 50, "min_visible": 1,
            "auto_replenish": True, "replenish_quantity": 1,
            "catalog_war": True, "floor_price": 99, "ceiling_price": 1499,
            "catalog_product_id": cpid,
        }
        with open("stock_config_raymundo.json","w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        if TG and TGCID:
            requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
                "chat_id":TGCID,"parse_mode":"Markdown",
                "text":f"✅ Publicado nuevo Go 3 Negro: `{new_iid}` (catálogo `{cpid}`)"}, timeout=20)
    else:
        print(f"  ❌ {j}")
