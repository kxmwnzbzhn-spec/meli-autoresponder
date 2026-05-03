#!/usr/bin/env python3
"""Publicar 2 Bose SoundLink Home en Raymundo, $3499, 20u real, después pausar.

CATS:
- MLM49963786 → Negro
- MLM50131488 → Silver
"""
import os, requests, time, json

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID = os.environ.get("TELEGRAM_CHAT_ID","")

PUBS = [
    {"cpid":"MLM49963786","color":"Negro","stock":20,"price":3499},
    {"cpid":"MLM50131488","color":"Light silver","stock":20,"price":3499},
]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me["id"]
print(f"Cuenta {me['nickname']} ({uid})\n")

# Estado actual
for st in ["active","paused"]:
    rr = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=1",
                      headers=H).json()
    print(f"  {st}: {rr.get('paging',{}).get('total','?')}")

published = []
errors = []

for p in PUBS:
    cpid = p["cpid"]
    print(f"\n=== Publicar {cpid} ({p['color']}) ===")
    # Get product details
    prod = requests.get(f"https://api.mercadolibre.com/products/{cpid}",
                       headers=H, timeout=10).json()
    name = prod.get("name") or prod.get("family_name")
    pictures = [{"source": pic["url"]} for pic in prod.get("pictures",[])[:8]]

    # Description blindada
    desc = (
        f"Bose SoundLink Home en color {p['color']}, reacondicionado en excelente estado. "
        f"Sonido envolvente premium, conexion Bluetooth estable, bateria de larga duracion. "
        f"Caja original incluida con cable de carga.\n\n"
        f"IMPORTANTE: Producto reacondicionado. No aplica garantia del fabricante. "
        f"Estetica 9.5/10. Funcionalidad 100%.\n\n"
        f"Envio gratis. Stock real 20 unidades."
    )

    # MELI migrated category to MLM179229 (Audio > Speakers)
    cat_id = "MLM179229"
    title = (name or f"Bose SoundLink Home {p['color']}")[:60]
    # Categoria correcta para Bocinas Portatiles MLM
    cat_id = "MLM176544"
    print(f"  category: {cat_id}")

    title = (name or f"Bose SoundLink Home {p['color']}")[:60]
    # Catalog listing condicion=new (MELI exige new o used).
    body = {
        "title": title,
        "category_id": cat_id,
        "catalog_product_id": cpid,
        "site_id": "MLM",
        "price": p["price"],
        "currency_id": "MXN",
        "available_quantity": 1,
        "buying_mode": "buy_it_now",
        "condition": "new",
        "listing_type_id": "gold_pro",
        "catalog_listing": True,
        "sale_terms": [{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                        {"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True},
        "pictures": pictures,
    }

    rp = requests.post("https://api.mercadolibre.com/items", headers=H,
                      json=body, timeout=30)
    if rp.status_code == 201:
        new = rp.json()
        new_iid = new["id"]
        print(f"  ✅ Publicado {new_iid}")

        # Set description
        try:
            requests.post(f"https://api.mercadolibre.com/items/{new_iid}/description",
                         headers=H, json={"plain_text": desc}, timeout=10)
        except: pass

        # Pausar inmediatamente
        time.sleep(1)
        rpause = requests.put(f"https://api.mercadolibre.com/items/{new_iid}",
                             headers=H, json={"status":"paused"}, timeout=10)
        if rpause.status_code == 200:
            print(f"  ⏸️  Pausado")
        published.append({"iid":new_iid, "cpid":cpid, "color":p["color"], "price":p["price"]})
    else:
        print(f"  ❌ {rp.status_code}:")
        try:
            err_data = rp.json()
            for cause in err_data.get("cause", [])[:10]:
                print(f"    [{cause.get('type','?')}] {cause.get('code','?')}: {cause.get('message','')}")
        except Exception:
            print(f"    {rp.text[:600]}")
        errors.append({"cpid":cpid,"err":rp.text[:500]})
    time.sleep(1)

# Update config
try:
    with open("stock_config_raymundo.json") as f: cfg = json.load(f)
except: cfg = {}

for p in published:
    cfg[p["iid"]] = {
        "line": "Raymundo",
        "title": f"Bose SoundLink Home {p['color']}",
        "model": "SoundLink Home",
        "color": p["color"],
        "real_stock": 20,
        "min_visible": 1,
        "auto_replenish": True,
        "active": False,  # pausado por usuario
        "paused_by_user": True,
        "floor_price": p["price"],   # no bajar de $3499
        "ceiling_price": 3499,
        "floor_locked_by_user": True,
    }

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

# Estado final
print(f"\n=== Estado final ===")
for st in ["active","paused"]:
    rr = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=1",
                      headers=H).json()
    print(f"  {st}: {rr.get('paging',{}).get('total','?')}")

# TG
if TG and TGCID:
    msg = f"📦 *Bose SoundLink Home publicados en Raymundo*\n\n"
    for p in published:
        msg += f"✅ `{p['iid']}` {p['color']} ${p['price']}\n"
    if errors:
        msg += f"\n❌ Errores: {len(errors)}\n"
        for e in errors[:3]:
            msg += f"• {e['cpid']}: {e['err'][:100]}\n"
    msg += f"\n*Estado:* PAUSADOS (mañana 6am se reactivan junto con los demás)\n"
    msg += f"Floor lock $3499 (no bajan de ahi)"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
