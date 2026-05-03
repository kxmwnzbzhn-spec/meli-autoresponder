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
H = {"Authorization": f"Bearer {r.json()['access_token']}"}

with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)

ITEMS = ["MLM2891189883", "MLM5246052014"]

for iid in ITEMS:
    print(f"\n{'='*70}\n=== {iid} ===")
    it = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=15).json()
    print(f"  title:           {it.get('title','?')[:80]}")
    print(f"  price actual:    ${it.get('price')}")
    print(f"  qty:             {it.get('available_quantity')}")
    print(f"  status:          {it.get('status')}")
    print(f"  catalog_listing: {it.get('catalog_listing')}")
    print(f"  cpid:            {it.get('catalog_product_id')}")

    # Stock config
    meta = cfg.get(iid, {})
    print(f"\n  CONFIG:")
    print(f"    label:        {meta.get('label')}")
    print(f"    model:        {meta.get('model')}")
    print(f"    color:        {meta.get('color')}")
    print(f"    floor_price:  ${meta.get('floor_price')}")
    print(f"    ceiling:      ${meta.get('ceiling_price')}")
    print(f"    catalog_war:  {meta.get('catalog_war')}")
    print(f"    real_stock:   {meta.get('real_stock')}")

    # price_to_win details
    ptw = requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2", headers=H, timeout=15).json()
    print(f"\n  PRICE_TO_WIN:")
    print(f"    status:          {ptw.get('status')}")
    print(f"    price_to_win:    ${ptw.get('price_to_win')}")
    print(f"    current_price:   ${ptw.get('current_price')}")
    if ptw.get("competitors"):
        print(f"    Competidores top:")
        for c in (ptw.get("competitors") or [])[:3]:
            print(f"      - ${c.get('price')} | {c.get('shipping')} | seller={c.get('seller_id')}")

    # Buy box info from catalog
    cpid = it.get("catalog_product_id")
    if cpid:
        bb = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=5", headers=H, timeout=15).json()
        print(f"\n  TOP BUY BOX OFFERS catálogo {cpid}:")
        for r in (bb.get("results") or [])[:5]:
            print(f"      ${r.get('price')} | seller={r.get('seller_id')} | logistic={r.get('shipping',{}).get('logistic_type')} | free={r.get('shipping',{}).get('free_shipping')}")

if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown",
        "text":"Diagnostico 2 items con precio bajo enviado al log."
    }, timeout=20)
