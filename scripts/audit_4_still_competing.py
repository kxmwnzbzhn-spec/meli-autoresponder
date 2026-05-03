#!/usr/bin/env python3
"""Auditoria detallada de los 4 items que siguen compitiendo despues del floor attack.
- Estado actual (price/status/condition)
- PTW completo (status, price_to_win, winners array)
- Catalog product_id + competidores en el catálogo
- Recomendación
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

ITEMS = [
    "MLM2904767845",
    "MLM5246052052",
    "MLM5246052128",
    "MLM5246077470",
]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}

reports = []
for iid in ITEMS:
    print(f"\n{'='*70}\n=== {iid} ===")
    it = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                      headers=H, timeout=10).json()
    title = it.get("title","")
    cur = it.get("price")
    cond = it.get("condition")
    cpid = it.get("catalog_product_id")
    fs = (it.get("shipping",{}) or {}).get("free_shipping")
    print(f"  title: {title[:75]}")
    print(f"  precio: ${cur} | condition: {cond} | cpid: {cpid} | free_ship: {fs}")

    # PTW v2 detallado
    ptw = requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
                       headers=H, timeout=10).json()
    print(f"  ptw_status: {ptw.get('status')}")
    print(f"  price_to_win: ${ptw.get('price_to_win')}")
    print(f"  winning_buy_box: {ptw.get('winning_buy_box')}")
    print(f"  current_price: ${ptw.get('current_price')}")

    # Catalog product detail (ver competidores)
    competidores = []
    if cpid:
        prod = requests.get(f"https://api.mercadolibre.com/products/{cpid}",
                            headers=H, timeout=10).json()
        bb = prod.get("buy_box_winner") or {}
        print(f"  buy_box_winner: ${bb.get('price')} seller_id={bb.get('seller_id')}")

        # Listar items del catalogo
        try:
            items_in_cat = requests.get(
                f"https://api.mercadolibre.com/products/{cpid}/items",
                headers=H, timeout=10, params={"limit":10}).json()
            results = items_in_cat.get("results", []) if isinstance(items_in_cat, dict) else []
            print(f"  competidores en catalog ({len(results)}):")
            for c in results[:8]:
                comp_iid = c.get("item_id") or c.get("id")
                comp_p = c.get("price")
                comp_seller = c.get("seller_id") or c.get("seller", {}).get("id") if isinstance(c.get("seller"), dict) else c.get("seller_id")
                comp_cond = c.get("condition")
                comp_fs = (c.get("shipping",{}) or {}).get("free_shipping")
                comp_ship = (c.get("shipping",{}) or {}).get("logistic_type")
                print(f"    • {comp_iid} ${comp_p} seller={comp_seller} cond={comp_cond} fs={comp_fs} log={comp_ship}")
                competidores.append({"iid":comp_iid,"price":comp_p,"seller":comp_seller,"cond":comp_cond,"fs":comp_fs})
        except Exception as e:
            print(f"  err items_in_cat: {e}")

    reports.append({"iid":iid,"title":title[:60],"cur":cur,"ptw":ptw,"cpid":cpid,"competidores":competidores})
    time.sleep(0.5)

# TG
if TG and TGCID:
    msg = "🔍 *Audit 4 items aún compitiendo*\n\n"
    for r in reports:
        st = r["ptw"].get("status","?")
        ptw_p = r["ptw"].get("price_to_win")
        msg += f"`{r['iid']}` ${r['cur']} st=*{st}* ptw=${ptw_p}\n"
        msg += f"  _{r['title']}_\n"
        for c in r["competidores"][:4]:
            ours = "👑" if c["iid"] == r["iid"] else "  "
            msg += f"  {ours} ${c['price']} seller={c['seller']} fs={c['fs']}\n"
        msg += "\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
