#!/usr/bin/env python3
# Consulta temporal autorizada de nombres de catálogo\nimport json
import os
import requests

API = "https://api.mercadolibre.com"
ITEMS = ["MLM3298045539", "MLM6014186110", "MLM6014186112"]

r = requests.post(f"{API}/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"],
}, timeout=20)
r.raise_for_status()
tok = r.json()
with open("/tmp/rocio_rotated_token", "w") as fh:
    fh.write(tok.get("refresh_token", ""))
H = {"Authorization": f"Bearer {tok['access_token']}"}

out = []
for iid in ITEMS:
    ir = requests.get(f"{API}/items/{iid}", headers=H, timeout=15)
    ir.raise_for_status()
    item = ir.json()
    cpid = item.get("catalog_product_id")
    product = {}
    if cpid:
        pr = requests.get(f"{API}/products/{cpid}", headers=H, timeout=15)
        pr.raise_for_status()
        product = pr.json()
    out.append({
        "item_id": iid,
        "listing_title": item.get("title"),
        "catalog_product_id": cpid,
        "catalog_name": product.get("name"),
        "catalog_status": product.get("status"),
        "permalink": product.get("permalink"),
    })
print("CATALOG_GO5_JSON=" + json.dumps(out, ensure_ascii=False), flush=True)
