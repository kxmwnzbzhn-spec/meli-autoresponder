#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"
APP_ID = os.environ["MELI_APP_ID_NEW"]
APP_SECRET = os.environ["MELI_APP_SECRET_NEW"]

def token(account):
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "refresh_token": os.environ[f"MELI_REFRESH_TOKEN_{account}"],
    }, timeout=20)
    r.raise_for_status()
    j = r.json()
    with open(f"/tmp/{account.lower()}_diag_rt", "w") as fh:
        fh.write(j.get("refresh_token", ""))
    return j["access_token"]

def stock(upid, H):
    r = requests.get(f"{API}/user-products/{upid}/stock", headers=H, timeout=15)
    return {"http": r.status_code, "version": r.headers.get("x-version"), "body": r.json() if r.text else {}}

def item(iid, H):
    r = requests.get(f"{API}/items/{iid}", headers=H, timeout=15)
    r.raise_for_status()
    x = r.json()
    out = {k: x.get(k) for k in ("id", "title", "seller_id", "status", "sub_status", "available_quantity", "inventory_id", "user_product_id", "catalog_product_id")}
    if x.get("user_product_id"):
        out["user_product_stock"] = stock(x["user_product_id"], H)
    return out

at = token("LUISED")
H = {"Authorization": f"Bearer {at}"}
luised = [item(i, H) for i in ["MLM3356000563", "MLM3356016605", "MLM3356013517", "MLM3355975897"]]

at = token("EDILBERTO")
H = {"Authorization": f"Bearer {at}"}
edilberto = {
    "MLMU4851933870": stock("MLMU4851933870", H),
    "MLM3355626501": item("MLM3355626501", H),
}

print("DIAG_JSON=" + json.dumps({"LuisEd": luised, "Edilberto": edilberto}, ensure_ascii=False), flush=True)
