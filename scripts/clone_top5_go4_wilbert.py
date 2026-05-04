"""Clonar las 5 Go 4 mas vendidas de Raymundo a Wilbert.
Mantiene catalog_product_id (catalog listing), condition, fotos.
Precio $449, stock visible 1, condition usado (reacond).
Despues de publicar, las deja ACTIVAS para que el user revise.
"""
import os, requests, time, json

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT_RAYMUNDO=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
RT_WILBERT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

# Batch CLIP 5 #4 final: posiciones 22-27 (6 publicaciones restantes)
SOURCES = [
    "MLM2904691275",  # 0 sold
    "MLM2904678391",  # 0 sold
    "MLM2904691353",  # 0 sold
    "MLM2904678397",  # 0 sold
    "MLM2904691313",  # 0 sold
    "MLM2904676579",  # 0 sold
]
PRICE = 699   # Clip 5 floor
VISIBLE_QTY = 1


def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

# 1. Auth Raymundo (source) y Wilbert (target)
at_r = tok(RT_RAYMUNDO)
at_w = tok(RT_WILBERT)
if not at_w:
    print("❌ NO se pudo autenticar Wilbert. Revisa MELI_REFRESH_TOKEN_WILBERT")
    exit(1)
H_r = {"Authorization": f"Bearer {at_r}"}
H_w = {"Authorization": f"Bearer {at_w}", "Content-Type":"application/json"}

me_w = requests.get("https://api.mercadolibre.com/users/me", headers=H_w).json()
print(f"Target: {me_w.get('nickname')} ({me_w.get('id')})\n")

results = []
for src_iid in SOURCES:
    print(f"\n=== {src_iid} ===")
    # Fetch source info
    src = requests.get(f"https://api.mercadolibre.com/items/{src_iid}", headers=H_r,
                       timeout=15).json()
    cpid = src.get("catalog_product_id")
    title = src.get("title","")
    condition = src.get("condition") or "used"
    cat_id = src.get("category_id")
    pictures = [{"source": p["url"]} for p in src.get("pictures",[])[:8]]
    print(f"  source: {title[:60]} | cpid={cpid} | cond={condition} | cat={cat_id}")

    if not cpid:
        results.append({"src":src_iid,"err":"no catalog_product_id"})
        print(f"  ❌ sin cpid, skip")
        continue

    # Build publish body
    body = {
        "title": title[:60],
        "catalog_product_id": cpid,
        "category_id": cat_id,
        "site_id": "MLM",
        "price": PRICE,
        "currency_id": "MXN",
        "available_quantity": VISIBLE_QTY,
        "buying_mode": "buy_it_now",
        "condition": condition,  # mantener el mismo (usado)
        "listing_type_id": "gold_pro",
        "catalog_listing": True,
        "sale_terms": [
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
        "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"xd_drop_off"},
        "pictures": pictures,
    }

    rp = requests.post("https://api.mercadolibre.com/items", headers=H_w,
                       json=body, timeout=30)
    if rp.status_code == 201:
        new = rp.json()
        new_iid = new["id"]
        print(f"  ✅ Publicado en Wilbert: {new_iid} → ${new.get('price')}")
        results.append({"src":src_iid,"new":new_iid,"title":title[:50],"price":PRICE,"ok":True})
    else:
        print(f"  ❌ {rp.status_code}:")
        try:
            err=rp.json()
            for c in err.get("cause",[])[:5]:
                print(f"     [{c.get('type')}] {c.get('code')}: {c.get('message')}")
        except: print(f"     {rp.text[:400]}")
        results.append({"src":src_iid,"err":rp.text[:300]})
    time.sleep(1)

print(f"\n{'='*60}\n=== RESUMEN ===")
for r in results:
    if r.get("ok"):
        print(f"  ✅ {r['src']} → {r['new']}  ${r['price']}  {r['title']}")
    else:
        print(f"  ❌ {r['src']}: {r.get('err','?')[:120]}")

# Telegram
if TG and TGCID:
    msg = f"🚀 *Clone Top 5 Go 4 Raymundo → Wilbert*\n\n"
    ok_count = sum(1 for r in results if r.get('ok'))
    msg += f"Publicadas: *{ok_count}/5*\n\n"
    for r in results:
        if r.get('ok'):
            msg += f"✅ `{r['new']}` ${r['price']}\n"
        else:
            msg += f"❌ `{r['src']}`: {r.get('err','?')[:80]}\n"
    msg += "\n*Activas* para revisar. Avisar si proceder con siguientes 5."
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
