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


# Reparación autorizada y verificación exacta del User Product agotado de Edilberto
before, version, raw = None, None, None
at = token("EDILBERTO")
H = {"Authorization": f"Bearer {at}"}
r0 = requests.get(f"{API}/user-products/MLMU4851933870/stock", headers=H, timeout=15)
before = r0.json()
version = r0.headers.get("x-version")
put_headers = {**H, "Content-Type": "application/json"}
if version:
    put_headers["x-version"] = version
rp = requests.put(
    f"{API}/user-products/MLMU4851933870/stock/type/selling_address",
    headers=put_headers,
    json={"quantity": 1},
    timeout=15,
)
r1 = requests.get(f"{API}/user-products/MLMU4851933870/stock", headers=H, timeout=15)
print("REPAIR_JSON=" + json.dumps({
    "before": before,
    "x_version": version,
    "put_http": rp.status_code,
    "put_body": rp.text,
    "after": r1.json(),
    "after_version": r1.headers.get("x-version"),
}, ensure_ascii=False), flush=True)


# Fallback compatible con MLM: localizar el item asociado al User Product y reponer por /items
at = token("EDILBERTO")
H = {"Authorization": f"Bearer {at}"}
HJ = {**H, "Content-Type": "application/json"}
uid = 3616975257
ids = []
offset = 0
while True:
    sr = requests.get(f"{API}/users/{uid}/items/search", headers=H, params={"limit": 50, "offset": offset}, timeout=15)
    sr.raise_for_status()
    batch = sr.json().get("results") or []
    ids.extend(batch)
    if len(batch) < 50:
        break
    offset += 50
associated = []
for start in range(0, len(ids), 20):
    mg = requests.get(f"{API}/items", headers=H, params={"ids": ",".join(ids[start:start+20])}, timeout=20)
    mg.raise_for_status()
    for row in mg.json():
        if row.get("code") == 200 and (row.get("body") or {}).get("user_product_id") == "MLMU4851933870":
            associated.append(row["body"])
repairs = []
for x in associated:
    body = {"available_quantity": 1}
    if x.get("status") == "paused":
        body["status"] = "active"
    rp = requests.put(f"{API}/items/{x['id']}", headers=HJ, json=body, timeout=15)
    repairs.append({"item_id": x["id"], "before_qty": x.get("available_quantity"), "before_status": x.get("status"), "http": rp.status_code, "response": rp.json() if rp.text else {}})
after_stock = requests.get(f"{API}/user-products/MLMU4851933870/stock", headers=H, timeout=15).json()
print("ITEM_FALLBACK_JSON=" + json.dumps({"associated": [{"id":x.get("id"),"title":x.get("title"),"status":x.get("status"),"qty":x.get("available_quantity")} for x in associated], "repairs": repairs, "after_stock": after_stock}, ensure_ascii=False), flush=True)
