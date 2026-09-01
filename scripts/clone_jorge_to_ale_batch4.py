#!/usr/bin/env python3
"""Clone the fourth three Jorge catalog listings to Alejandra, idempotently."""
import json, os, requests

API = "https://api.mercadolibre.com"
SOURCE_IDS = ["MLM3403250729", "MLM3409049385", "MLM3409086281"]
SOURCE_SELLER = 3640697853
TARGET_SELLER = 3629038896
TIMEOUT = 30

def refresh(secret_name, output_path):
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ[secret_name],
    }, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    open(output_path, "w").write(data["refresh_token"])
    return data["access_token"]

source_access = refresh("MELI_REFRESH_TOKEN_JORGE_LUIS", "/tmp/jorge_luis_rotated_token")
target_access = refresh("MELI_REFRESH_TOKEN_ALE", "/tmp/ale_rotated_token")
HS = {"Authorization": f"Bearer {source_access}"}
HT = {"Authorization": f"Bearer {target_access}"}
HTJ = {**HT, "Content-Type": "application/json"}

def get_item(item_id, seller_id, headers):
    rr = requests.get(f"{API}/items/{item_id}", headers=headers, timeout=TIMEOUT)
    rr.raise_for_status()
    item = rr.json()
    if int(item.get("seller_id") or 0) != seller_id:
        raise RuntimeError(f"{item_id}: seller {item.get('seller_id')} != {seller_id}")
    return item

def target_ids():
    offset = 0
    while True:
        rr = requests.get(f"{API}/users/{TARGET_SELLER}/items/search", headers=HT,
                          params={"limit": 100, "offset": offset}, timeout=TIMEOUT)
        rr.raise_for_status()
        batch = rr.json().get("results") or []
        yield from batch
        if len(batch) < 100:
            return
        offset += 100

def existing_for(source):
    catalog = source.get("catalog_product_id")
    condition = source.get("condition")
    for item_id in target_ids():
        try:
            item = get_item(item_id, TARGET_SELLER, HT)
        except Exception:
            continue
        if (item.get("catalog_product_id") == catalog and
            item.get("condition") == condition and
            bool(item.get("catalog_listing")) and not item.get("deleted")):
            return item
    return None

def copy_attrs(source):
    out = []
    seen = set()
    for attr in source.get("attributes") or []:
        aid = attr.get("id")
        if aid not in {"GTIN", "EAN", "UPC", "ITEM_CONDITION", "GRADING"} or aid in seen:
            continue
        value_name = attr.get("value_name")
        if aid in {"GTIN", "EAN", "UPC"}:
            value = str(value_name or "").strip()
            if not (value.isdigit() and 8 <= len(value) <= 14):
                continue
            aid = "GTIN"
        copied = {"id": aid}
        if attr.get("value_id"):
            copied["value_id"] = attr["value_id"]
        if value_name:
            copied["value_name"] = value_name
        out.append(copied)
        seen.add(aid)
    if "ITEM_CONDITION" not in seen:
        out.append({"id": "ITEM_CONDITION", "value_name": {
            "new": "Nuevo", "used": "Usado", "refurbished": "Reacondicionado"
        }[source["condition"]]})
    return out

def clone(source):
    if not source.get("catalog_product_id") or not source.get("catalog_listing"):
        raise RuntimeError(f"{source['id']}: no es publicación de catálogo")
    if source.get("condition") not in {"new", "used", "refurbished"}:
        raise RuntimeError(f"{source['id']}: condición inválida {source.get('condition')}")
    existing = existing_for(source)
    if existing:
        rr = requests.put(f"{API}/items/{existing['id']}", headers=HTJ, json={
            "price": source["price"], "available_quantity": 1, "status": "active"
        }, timeout=TIMEOUT)
        if rr.status_code not in (200, 201):
            raise RuntimeError(f"{existing['id']}: reuse failed {rr.status_code} {rr.text[:800]}")
        return existing["id"], "reused"
    shipping = source.get("shipping") or {}
    payload = {
        "site_id": "MLM",
        "family_name": (source.get("family_name") or source.get("title") or "Producto")[:60],
        "category_id": source["category_id"],
        "price": source["price"],
        "currency_id": source.get("currency_id") or "MXN",
        "available_quantity": 1,
        "buying_mode": source.get("buying_mode") or "buy_it_now",
        "listing_type_id": source.get("listing_type_id") or "gold_special",
        "condition": source["condition"],
        "catalog_product_id": source["catalog_product_id"],
        "catalog_listing": True,
        "attributes": copy_attrs(source),
        "shipping": {
            "mode": "me2",
            "local_pick_up": bool(shipping.get("local_pick_up")),
            "free_shipping": bool(shipping.get("free_shipping")),
        },
    }
    terms = []
    for term in source.get("sale_terms") or []:
        if term.get("id") in {"WARRANTY_TYPE", "WARRANTY_TIME"}:
            x = {"id": term["id"]}
            if term.get("value_id"): x["value_id"] = term["value_id"]
            if term.get("value_name"): x["value_name"] = term["value_name"]
            terms.append(x)
    if terms:
        payload["sale_terms"] = terms
    rr = requests.post(f"{API}/items", headers=HTJ, json=payload, timeout=45)
    print(f"POST source={source['id']} HTTP={rr.status_code} BODY={rr.text[:1200]}", flush=True)
    if rr.status_code not in (200, 201):
        raise RuntimeError(f"{source['id']}: publish failed {rr.status_code} {rr.text[:1600]}")
    return rr.json()["id"], "created"

results = []
for source_id in SOURCE_IDS:
    source = get_item(source_id, SOURCE_SELLER, HS)
    target_id, action = clone(source)
    target = get_item(target_id, TARGET_SELLER, HT)
    checks = {
        "active": target.get("status") == "active",
        "quantity_one": int(target.get("available_quantity") or 0) == 1,
        "same_price": float(target.get("price") or 0) == float(source.get("price") or 0),
        "same_condition": target.get("condition") == source.get("condition"),
        "same_catalog": target.get("catalog_product_id") == source.get("catalog_product_id"),
        "catalog_listing": bool(target.get("catalog_listing")),
    }
    if not all(checks.values()):
        raise RuntimeError(f"{target_id}: verification failed {checks}")
    results.append({
        "source_id": source_id, "target_id": target_id, "action": action,
        "title": target.get("title"), "price": target.get("price"),
        "condition": target.get("condition"), "status": target.get("status"),
        "quantity": target.get("available_quantity"), "permalink": target.get("permalink")
    })
print("ALE_BATCH4_RESULTS=" + json.dumps(results, ensure_ascii=False), flush=True)
