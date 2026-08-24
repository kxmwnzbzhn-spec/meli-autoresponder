#!/usr/bin/env python3
"""Valida y publica catálogos JBL Go 4 negros en Edilberto sin coincidencias aproximadas."""
import json
import os
import re
import time
import unicodedata
import requests

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
APPLY = os.environ.get("APPLY", "false").lower() == "true"
PRICE = float(os.environ.get("PRICE", "520"))

REQUESTS = [
    ("FE238", "Jbl Go Jbl Go 4 Go4 Negro"),
    ("FE239", "Altavoz Portátil Go 4 Con Bluetooth En Color Negro"),
    ("FE240", "Jbl Go 4 Bocina Bluetooth Portátil Impermeable Ip67 Negra Negro"),
    ("FE241", "Bocina JBL Go JBLGO4BLK GO4 portátil con bluetooth waterproof negra"),
    ("FE242", "Bocina JBL Go JBL GO 4 GO4 portátil con bluetooth waterproof negra"),
    ("FE243", "JBL Go 4 Bocina Bluetooth Portátil Impermeable IP67 Negra"),
    ("FE244", "Parlante JBL Go JBL GO 4 GO4 portátil con bluetooth waterproof negro"),
    ("FE245", "Bocina JBL GO4 portátil con bluetooth waterproof negra"),
    ("FE246", "Parlante JBL Go JBLGO4BLK GO4 portátil con bluetooth waterproof negro"),
    ("FE247", "Altavoz portátil Jbl Go4 con Bluetooth impermeable negro"),
    ("FE248", "Altavoz portátil Jbl Go4 con Bluetooth impermeable negro"),
    ("FE249", "Altavoz portátil Go 4 con Bluetooth en color negro"),
    ("FE250", "Parlante Jbl Go 4 Portátil Bluetooth Waterproof Negro"),
    ("FE251", "Parlante Inalámbrico Jbl Go 4 Bluetooth Ip67 Negro"),
    ("FE252", "Jbl Go 4 - Altavoz Bluetooth ultraportátil de color negro"),
    ("FE253", "JBL Go 4 Bocina Bluetooth Portátil Impermeable IP67 Negra"),
    ("FE254", "Bocina Jbl Go 4 Portátil Bluetooth - Color Variado Color Negro"),
    ("FE255", "Jbl Go 4 Portable Bluetooth Speaker Black Waterproof Color Negro"),
]

def norm(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

def refresh():
    response = requests.post(f"{API}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    }, timeout=25)
    response.raise_for_status()
    token = response.json()
    with open("/tmp/edilberto_rotated_token", "w") as fh:
        fh.write(token.get("refresh_token", ""))
    return token["access_token"]

TOKEN = refresh()
H = {"Authorization": f"Bearer {TOKEN}"}
HJ = {**H, "Content-Type": "application/json"}

me = requests.get(f"{API}/users/me", headers=H, timeout=20)
me.raise_for_status()
profile = me.json()
if int(profile.get("id") or 0) != SELLER_ID:
    raise SystemExit(f"Cuenta incorrecta: {profile.get('id')} {profile.get('nickname')}")
print(f"[ACCOUNT] {profile.get('nickname')} id={profile.get('id')} apply={APPLY} price={PRICE}", flush=True)

def api_get(path, params=None):
    for attempt in range(4):
        response = requests.get(f"{API}{path}", headers=H, params=params, timeout=25)
        if response.status_code != 429:
            return response
        time.sleep(2 ** attempt)
    return response

def validate_product(product):
    name = product.get("name") or ""
    attrs = {a.get("id"): a.get("value_name") for a in (product.get("attributes") or [])}
    brand = norm(attrs.get("BRAND") or name)
    model = norm(attrs.get("MODEL") or name).replace(" ", "")
    color = norm(attrs.get("COLOR") or name)
    issues = []
    if "jbl" not in brand:
        issues.append(f"brand={attrs.get('BRAND')}")
    if "go4" not in model:
        issues.append(f"model={attrs.get('MODEL')}")
    if not any(word in color for word in ("negro", "negra", "black")):
        issues.append(f"color={attrs.get('COLOR')}")
    return issues, attrs

# Catálogos que Edilberto ya tiene, para no duplicar ofertas del mismo catálogo.
existing_cpids = {}
offset = 0
while True:
    response = api_get(f"/users/{SELLER_ID}/items/search", {"limit": 100, "offset": offset})
    response.raise_for_status()
    data = response.json()
    ids = data.get("results") or []
    for start in range(0, len(ids), 20):
        chunk = ids[start:start+20]
        multi = api_get("/items", {"ids": ",".join(chunk), "attributes": "id,title,status,catalog_product_id,condition"})
        multi.raise_for_status()
        for row in multi.json():
            body = row.get("body") or {}
            cpid = body.get("catalog_product_id")
            if cpid and body.get("status") not in ("closed",):
                existing_cpids.setdefault(cpid, []).append(body.get("id"))
    offset += len(ids)
    if not ids or offset >= int((data.get("paging") or {}).get("total") or 0):
        break

selected = []
used_cpids = set()
unmatched = []
for invoice, requested_title in REQUESTS:
    response = api_get("/products/search", {
        "site_id": "MLM", "status": "active", "q": requested_title, "limit": 50,
    })
    response.raise_for_status()
    candidates = []
    for row in response.json().get("results") or []:
        cpid = row.get("id")
        if not cpid or cpid.startswith("MLMU"):
            continue
        detail_response = api_get(f"/products/{cpid}")
        if detail_response.status_code != 200:
            continue
        detail = detail_response.json()
        if norm(detail.get("name")) != norm(requested_title):
            continue
        issues, attrs = validate_product(detail)
        if issues:
            print(f"[REJECT] {invoice} {cpid} title={detail.get('name')!r} issues={issues}", flush=True)
            continue
        candidates.append((cpid, detail, attrs))
        time.sleep(0.15)

    # La misma factura/título puede corresponder a catálogos duplicados; no reutilizar CPID.
    available = [c for c in candidates if c[0] not in used_cpids and c[0] not in existing_cpids]
    if not available:
        already = [c for c in candidates if c[0] in existing_cpids]
        if already:
            cpid, detail, attrs = already[0]
            print(f"[ALREADY] {invoice} {cpid} items={existing_cpids[cpid]} title={detail.get('name')!r}", flush=True)
            used_cpids.add(cpid)
            selected.append({"invoice": invoice, "cpid": cpid, "title": detail.get("name"), "already": True})
            continue
        print(f"[NO-EXACT-MATCH] {invoice} requested={requested_title!r} exact_candidates={[c[0] for c in candidates]}", flush=True)
        unmatched.append({"invoice": invoice, "title": requested_title, "candidates": [c[0] for c in candidates]})
        continue
    cpid, detail, attrs = available[0]
    used_cpids.add(cpid)
    selected.append({"invoice": invoice, "cpid": cpid, "title": detail.get("name"), "already": False})
    print(f"[MATCH] {invoice} -> {cpid} exact_title={detail.get('name')!r} color={attrs.get('COLOR')} model={attrs.get('MODEL')}", flush=True)

print(f"[VALIDATION] requested={len(REQUESTS)} matched={len(selected)} unmatched={len(unmatched)}", flush=True)
if unmatched:
    print("[STOP] No se publica parcialmente porque existen títulos sin coincidencia exacta.", flush=True)
    with open("/tmp/edilberto_go4_results.json", "w") as fh:
        json.dump({"selected": selected, "unmatched": unmatched, "published": []}, fh, ensure_ascii=False, indent=2)
    raise SystemExit(2)
if not APPLY:
    print("[DRY-RUN-OK] Todas las facturas tienen catálogo exacto; falta ejecutar APPLY=true.", flush=True)
    with open("/tmp/edilberto_go4_results.json", "w") as fh:
        json.dump({"selected": selected, "unmatched": [], "published": []}, fh, ensure_ascii=False, indent=2)
    raise SystemExit(0)

published = []
for entry in selected:
    if entry["already"]:
        continue
    cpid = entry["cpid"]
    product_response = api_get(f"/products/{cpid}")
    product_response.raise_for_status()
    product = product_response.json()
    offers_response = api_get(f"/products/{cpid}/items", {"limit": 50})
    offers_response.raise_for_status()
    offers = offers_response.json().get("results") or []
    category_id = None
    for offer in offers:
        iid = offer.get("item_id")
        if not iid:
            continue
        ref = api_get(f"/items/{iid}", {"attributes": "category_id"})
        if ref.status_code == 200:
            category_id = ref.json().get("category_id")
            if category_id:
                break
    if not category_id:
        category_id = (product.get("category_details") or {}).get("id")
    if not category_id:
        raise RuntimeError(f"{entry['invoice']} {cpid}: sin category_id")

    exact_title = product.get("name") or ""
    payload = {
        "site_id": "MLM",
        "title": exact_title[:60],
        "category_id": category_id,
        "catalog_product_id": cpid,
        "catalog_listing": True,
        "price": PRICE,
        "available_quantity": 1,
        "condition": "new",
        "listing_type_id": "gold_special",
        "currency_id": "MXN",
        "buying_mode": "buy_it_now",
        "sale_terms": [
            {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
            {"id": "WARRANTY_TIME", "value_name": "30 días"},
        ],
        "shipping": {"mode": "me2", "local_pick_up": False, "free_shipping": False},
    }
    created_response = requests.post(f"{API}/items", headers=HJ, json=payload, timeout=35)
    if created_response.status_code not in (200, 201):
        raise RuntimeError(f"{entry['invoice']} {cpid}: POST {created_response.status_code} {created_response.text[:800]}")
    created = created_response.json()
    iid = created.get("id")
    verify_response = api_get(f"/items/{iid}")
    verify_response.raise_for_status()
    verify = verify_response.json()
    exact = (
        verify.get("catalog_product_id") == cpid
        and verify.get("condition") == "new"
        and norm(verify.get("title")) == norm(exact_title)
        and int(verify.get("available_quantity") or 0) == 1
    )
    if not exact:
        requests.put(f"{API}/items/{iid}", headers=HJ, json={"status": "paused"}, timeout=20)
        raise RuntimeError(
            f"{entry['invoice']} {iid}: verificación falló "
            f"title={verify.get('title')!r} condition={verify.get('condition')} "
            f"cpid={verify.get('catalog_product_id')} qty={verify.get('available_quantity')}"
        )
    published.append({"invoice": entry["invoice"], "cpid": cpid, "item_id": iid, "title": verify.get("title"), "condition": "new", "price": verify.get("price")})
    print(f"[PUBLISHED-VERIFIED] {entry['invoice']} {iid} cpid={cpid} title={verify.get('title')!r} condition=new price={verify.get('price')}", flush=True)
    time.sleep(1.5)

with open("/tmp/edilberto_go4_results.json", "w") as fh:
    json.dump({"selected": selected, "unmatched": [], "published": published}, fh, ensure_ascii=False, indent=2)
print(f"[DONE] verified={len(published)} already={sum(1 for x in selected if x['already'])}", flush=True)
