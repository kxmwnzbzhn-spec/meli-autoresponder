#!/usr/bin/env python3
"""Inspeccionar 2 catalogos MELI para saber que son."""
import os, requests, json

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}

CATS = ["MLM49963786", "MLM50131488"]

for cpid in CATS:
    print(f"\n{'='*70}\n=== {cpid} ===")
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}",
                     headers=H, timeout=10).json()
    print(f"name: {p.get('name')}")
    print(f"category_id: {p.get('category_id')}")
    print(f"domain_id: {p.get('domain_id')}")
    print(f"family_name: {p.get('family_name')}")
    bb = p.get("buy_box_winner") or {}
    print(f"buy_box_winner: ${bb.get('price')} / seller {bb.get('seller_id')}")
    # main attributes
    attrs = {a["id"]: a.get("value_name") for a in p.get("attributes",[])}
    for k in ["BRAND","MODEL","COLOR","ITEM_CONDITION","GTIN","DETAILED_MODEL","LINE"]:
        if k in attrs: print(f"  {k}: {attrs[k]}")
    # pictures
    pics = p.get("pictures",[])
    print(f"pictures: {len(pics)}")
    if pics: print(f"  first: {pics[0].get('url','')[:90]}")
    # listed prices in catalog
    try:
        items = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items",
                            headers=H, timeout=10, params={"limit":5}).json()
        results = items.get("results",[]) if isinstance(items, dict) else []
        print(f"competidores ({len(results)}):")
        for c in results[:5]:
            print(f"  ${c.get('price')} cond={c.get('condition')} fs={(c.get('shipping') or {}).get('free_shipping')}")
    except Exception as e:
        print(f"items err: {e}")
