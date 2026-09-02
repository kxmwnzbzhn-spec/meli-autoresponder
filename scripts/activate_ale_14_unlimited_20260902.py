#!/usr/bin/env python3
import json
import requests

API = "https://api.mercadolibre.com"
SELLER = 3629038896
IDS = [
    "MLM3438301245", "MLM3438301787", "MLM3438313975", "MLM3438302291",
    "MLM3438302099", "MLM6154083792", "MLM3438314633", "MLM6154007142",
    "MLM6154007138", "MLM6154083626", "MLM3438299333", "MLM6154083256",
    "MLM3438301603", "MLM3438302377",
]
access = open("/tmp/ale_access_token").read().strip()
headers = {"Authorization": f"Bearer {access}"}
json_headers = {**headers, "Content-Type": "application/json"}

me = requests.get(f"{API}/users/me", headers=headers, timeout=25)
me.raise_for_status()
if int(me.json()["id"]) != SELLER:
    raise RuntimeError(f"Token no corresponde a Alejandra: {me.json()['id']}")

results = []
for item_id in IDS:
    before = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=25)
    before.raise_for_status()
    item = before.json()
    if int(item.get("seller_id") or 0) != SELLER:
        raise RuntimeError(f"{item_id} no pertenece a Alejandra")
    update = requests.put(
        f"{API}/items/{item_id}",
        headers=json_headers,
        json={"available_quantity": 1, "status": "active"},
        timeout=25,
    )
    if update.status_code not in (200, 201):
        raise RuntimeError(f"{item_id}: PUT {update.status_code} {update.text[:400]}")
    after = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=25)
    after.raise_for_status()
    final = after.json()
    row = {
        "id": item_id,
        "title": final.get("title"),
        "status": final.get("status"),
        "qty": final.get("available_quantity"),
        "sub_status": final.get("sub_status"),
    }
    results.append(row)
    if row["status"] != "active" or int(row["qty"] or 0) != 1:
        raise RuntimeError(f"Verificacion fallo: {json.dumps(row, ensure_ascii=False)}")

print("ALE_14_AUTOSTOCK_RESULT=" + json.dumps(results, ensure_ascii=False))
print("ALE_14_AUTOSTOCK_CONFIRMED=true")
