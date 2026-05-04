#!/usr/bin/env python3
"""Diag profundo de items Wilbert en floor_block — competidor real, FULL?, precio."""
import os, json, requests, re, time
API="https://api.mercadolibre.com"

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]

def refresh():
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
        "client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=20)
    return r.json()["access_token"]

tok=refresh()
H={"Authorization":f"Bearer {tok}"}

# Items en floor_block detectados en última corrida
TARGETS = [
 "MLM5287495718","MLM5287380274","MLM5287366416","MLM5287368920","MLM5287368936",
 "MLM5287354124","MLM5287354126","MLM5287354114","MLM5287362240","MLM2907544761",
 "MLM5287355602","MLM2907545885"
]

print(f"{'iid':<14} {'price':>5} {'ptw':>5} {'cpid':<14} {'winner_seller':>14} {'winner_price':>12} {'logistic':>12}")
for iid in TARGETS:
    try:
        it=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
        cur=it.get("price"); cpid=it.get("catalog_product_id"); status=it.get("status")
        pt=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=15).json()
        ptw=pt.get("price_to_win") or pt.get("ptw")
        # buy box winner del catálogo
        bbw_seller=""; bbw_price=""; bbw_log=""
        if cpid:
            p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
            bbw=p.get("buy_box_winner",{}) or {}
            bbw_seller=str(bbw.get("seller_id",""))
            bbw_price=str(bbw.get("price",""))
            bbw_log=str(bbw.get("logistic_type",""))
        print(f"{iid:<14} {cur:>5} {str(ptw):>5} {str(cpid):<14} {bbw_seller:>14} {bbw_price:>12} {bbw_log:>12}")
        # Detalle si hay seller info en pt
        # print("  pt:", json.dumps(pt)[:300])
    except Exception as e:
        print(f"{iid} ERR {e}")
    time.sleep(0.2)

print("\n=== Detalle JSON ptw[0] ===")
pt=requests.get(f"{API}/items/{TARGETS[0]}/price_to_win?version=v2",headers=H,timeout=15).json()
print(json.dumps(pt,indent=2)[:1500])
