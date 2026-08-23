#!/usr/bin/env python3
"""Mantiene una unidad visible en las publicaciones autorizadas de Edilberto.
Validado para ejecución continua cada 30 segundos y prueba inicial controlada.
"""
import os
import time
import requests
from stock_policy import item_stock_action

API = "https://api.mercadolibre.com"
SELLER_ID = 3616975257
TARGETS = [
    "MLMU4851933870",
    "MLM3355626501",
    "MLM6042921636",
    "MLM6043044650",
    "MLM6042920630",
    "MLM6042920954",
    "MLM6042921184",
    "MLM3376191333",
    "MLM6061828546",
    "MLM6061793358",
    "MLM6061831150",
    "MLM6061856108",
    "MLM6061793370",
]
# Límites físicos por publicación; se llenan al validar las nuevas clonaciones.
REAL_STOCK_LIMITS = {
    "MLM6061828546": 500,
    "MLM6061793358": 28,
    "MLM6061831150": 28,
    "MLM6061856108": 6,
    "MLM6061793370": 16,
}
WAR_SOURCE_ITEMS = [
    "MLM6042921636",
    "MLM6043044650",
    "MLM6042920630",
    "MLM6042920954",
    "MLM6042921184",
]
PRICE_CEILINGS = {
    "MLM6042921636": 699,
    "MLM6043044650": 699,
    "MLM6042920630": 699,
    "MLM6042920954": 699,
    "MLM6042921184": 699,
}
PRICE_FLOOR = 499
PRICE_STEP = 10
ENABLE_PRICE_WAR = os.environ.get("ENABLE_PRICE_WAR","").strip().lower() == "true"
WIN_STREAK_REQUIRED = 4
WIN_STREAKS = {}
SYNC_REPAIR_AT = {}
FALLBACK_ITEMS = {
    "MLMU4851933870": ["MLM3355625791", "MLM3355650889"],
    "MLMU4821841613": ["MLM3355626501"],
    "MLMU4878756300": ["MLM6042921636"],
    "MLMU4848144839": ["MLM6043044650"],
    "MLMU4878694228": ["MLM6042920630"],
    "MLMU4878703120": ["MLM6042920954"],
    "MLMU4848196489": ["MLM6042921184"],
    # User-product IDs de las cuatro clonaciones nuevas de LuisEd.
    "MLMU4913863678": ["MLM6061793358"],
    "MLMU4913863698": ["MLM6061856108"],
    "MLMU4913876972": ["MLM6061793370"],
    "MLMU4913790954": ["MLM6061828546"],
    "MLMU4882549239": ["MLM3376191333"],
    "MLMU4913876936": ["MLM6061831150"],
}
TICK = 30
DURATION = int(os.environ.get("RUN_DURATION_SEC", str(5 * 3600 + 30 * 60)))

def refresh():
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID_NEW"],
        "client_secret": os.environ["MELI_APP_SECRET_NEW"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_EDILBERTO"],
    }, timeout=20)
    r.raise_for_status()
    return r.json()

tok = refresh()
with open("/tmp/edilberto_rotated_token", "w") as fh:
    fh.write(tok.get("refresh_token", ""))
H = {"Authorization": f"Bearer {tok['access_token']}"}
HJ = {**H, "Content-Type": "application/json"}

def paid_units_for_item(item_id):
    """Suma unidades de órdenes pagadas/no canceladas para este item."""
    total_units = 0
    offset = 0
    limit = 50
    while True:
        response = requests.get(
            f"{API}/orders/search",
            headers=H,
            params={
                "seller": SELLER_ID,
                "q": item_id,
                "limit": limit,
                "offset": offset,
                "sort": "date_asc",
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"{item_id}: orders search {response.status_code} "
                f"{response.text[:300]}"
            )
        data = response.json()
        rows = data.get("results") or []
        for order in rows:
            if order.get("status") in {"cancelled", "invalid"}:
                continue
            tags = set(order.get("tags") or [])
            approved_payment = any(
                payment.get("status") == "approved"
                for payment in (order.get("payments") or [])
            )
            if (
                order.get("status") not in {"paid", "partially_refunded"}
                and "paid" not in tags
                and not approved_payment
            ):
                continue
            for order_item in order.get("order_items") or []:
                if (order_item.get("item") or {}).get("id") == item_id:
                    total_units += int(order_item.get("quantity") or 0)
        paging = data.get("paging") or {}
        offset += len(rows)
        if not rows or offset >= int(paging.get("total") or 0):
            break
    return total_units


def enforce_real_stock(item_id, initial=False):
    """Devuelve True si aún se puede mostrar una unidad; pausa al agotarse."""
    initial_stock = REAL_STOCK_LIMITS.get(item_id)
    if initial_stock is None:
        return True
    sold_units = paid_units_for_item(item_id)
    remaining = max(0, int(initial_stock) - sold_units)
    if initial or remaining <= 2:
        print(
            f"[REAL-STOCK] {item_id} initial={initial_stock} "
            f"sold={sold_units} remaining={remaining}",
            flush=True,
        )
    if remaining > 0:
        return True
    item_response = requests.get(
        f"{API}/items/{item_id}", headers=H, timeout=15
    )
    item_response.raise_for_status()
    item = item_response.json()
    if item.get("status") != "paused":
        paused = requests.put(
            f"{API}/items/{item_id}",
            headers=HJ,
            json={"status": "paused"},
            timeout=20,
        )
        if paused.status_code not in (200, 201):
            raise RuntimeError(
                f"{item_id}: pause {paused.status_code} {paused.text[:300]}"
            )
        print(
            f"[REAL-STOCK-PAUSED] {item_id} sold={sold_units} "
            f"initial={initial_stock}",
            flush=True,
        )
    return False


def get_stock(upid):
    r = requests.get(f"{API}/user-products/{upid}/stock", headers=H, timeout=15)
    if r.status_code != 200:
        return None, None, r
    return r.json(), r.headers.get("x-version"), r

def keep_one_user_product(upid, initial=False):
    stock, version, raw = get_stock(upid)
    if stock is None:
        raise RuntimeError(f"{upid}: stock GET {raw.status_code} {raw.text[:250]}")
    if int(stock.get("user_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{upid}: user_id inesperado {stock.get('user_id')}")
    locations = stock.get("locations") or []
    editable = [x for x in locations if x.get("type") != "meli_facility"]
    if not editable:
        raise RuntimeError(f"{upid}: solo tiene stock Full; MELI controla sus existencias")
    total = sum(int(x.get("quantity") or 0) for x in editable)
    kinds = sorted({x.get("type") for x in editable})
    if total == 1:
        if initial:
            print(f"[OK-UP] {upid} editable_qty=1 types={kinds}", flush=True)
        return
    if len(kinds) != 1:
        raise RuntimeError(f"{upid}: tipos editables mixtos {kinds}")
    kind = kinds[0]
    keeper = max(range(len(editable)), key=lambda i: int(editable[i].get("quantity") or 0))
    headers = dict(HJ)
    if version:
        headers["x-version"] = version
    url = f"{API}/user-products/{upid}/stock/type/{kind}"
    if kind == "seller_warehouse":
        out = []
        for i, loc in enumerate(editable):
            row = {"quantity": 1 if i == keeper else 0}
            if loc.get("store_id") is not None:
                row["store_id"] = loc.get("store_id")
            if loc.get("network_node_id") is not None:
                row["network_node_id"] = loc.get("network_node_id")
            out.append(row)
        body = {"locations": out}
    elif kind == "selling_address":
        body = {"quantity": 1}
    else:
        raise RuntimeError(f"{upid}: tipo de stock no soportado {kind}")
    u = requests.put(url, headers=headers, json=body, timeout=15)
    if u.status_code not in (200, 201, 204):
        blocked = u.status_code == 400 and "blocked for modifications to the selling address" in u.text
        fallback = FALLBACK_ITEMS.get(upid) or []
        if not blocked or not fallback:
            raise RuntimeError(f"{upid}: stock PUT {u.status_code} {u.text[:300]}")
        repaired = []
        for iid in fallback:
            current = requests.get(f"{API}/items/{iid}", headers=H, timeout=15).json()
            action=item_stock_action(current.get("status"),current.get("sub_status"),current.get("available_quantity"))
            if action == "skip_non_sellable":
                print(f"[POLICY-SKIP-FALLBACK] {iid} status={current.get('status')} sub={current.get('sub_status')}",flush=True)
                continue
            item_body = {"available_quantity": 1}
            if action == "replenish_out_of_stock":
                item_body["status"] = "active"
            ri = requests.put(f"{API}/items/{iid}", headers=HJ, json=item_body, timeout=15)
            if ri.status_code not in (200, 201):
                raise RuntimeError(f"{upid}/{iid}: fallback PUT {ri.status_code} {ri.text[:300]}")
            repaired.append(iid)
        if not repaired:
            return
        verify, _, _ = get_stock(upid)
        new_total = sum(int(x.get("quantity") or 0) for x in (verify.get("locations") or []) if x.get("type") != "meli_facility")
        if new_total != 1:
            raise RuntimeError(f"{upid}: fallback ejecutado pero qty verificada={new_total}")
        print(f"[REPLENISHED-ITEM-FALLBACK] {upid} editable_qty {total}->1 items={repaired}", flush=True)
        return
    print(f"[REPLENISHED-UP] {upid} editable_qty {total}->1 type={kind}", flush=True)

def keep_one_item(item_id, initial=False):
    r = requests.get(f"{API}/items/{item_id}", headers=H, timeout=15)
    r.raise_for_status()
    item = r.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    if initial:
        competition = requests.get(
            f"{API}/items/{item_id}/price_to_win",
            headers=H,
            params={"version": "v2"},
            timeout=15,
        )
        competition_data = competition.json() if competition.status_code == 200 else {
            "http": competition.status_code,
            "body": competition.text[:300],
        }
        print(
            f"[CATALOG-INSPECT] {item_id} title={item.get('title','')} "
            f"price={item.get('price')} status={item.get('status')} "
            f"catalog_product_id={item.get('catalog_product_id')} "
            f"competition={competition_data}",
            flush=True,
        )
    upid = item.get("user_product_id")
    if upid:
        stock, _, raw = get_stock(upid)
        if stock is not None and any(x.get("type") != "meli_facility" for x in (stock.get("locations") or [])):
            keep_one_user_product(upid, initial=initial)
            action=item_stock_action(item.get("status"),item.get("sub_status"),item.get("available_quantity"))
            if action == "replenish_out_of_stock":
                u = requests.put(f"{API}/items/{item_id}", headers=HJ, json={"status": "active"}, timeout=15)
                if u.status_code not in (200, 201):
                    raise RuntimeError(f"{item_id}: reactivar {u.status_code} {u.text[:250]}")
                print(f"[REACTIVATED-OUT-OF-STOCK] {item_id}", flush=True)
            elif action == "skip_non_sellable":
                print(f"[POLICY-SKIP] {item_id} status={item.get('status')} sub={item.get('sub_status')}",flush=True)
            return
    if item.get("inventory_id"):
        raise RuntimeError(f"{item_id}: publicación Full; MELI controla sus existencias")
    if item.get("variations"):
        raise RuntimeError(f"{item_id}: tiene variaciones; requiere configuración individual")
    qty = int(item.get("available_quantity") or 0)
    status = item.get("status")
    action=item_stock_action(status,item.get("sub_status"),qty)
    if action == "noop":
        if initial:
            print(f"[OK] {item_id} active qty=1 title={item.get('title','')}", flush=True)
        return
    if action == "skip_non_sellable":
        if initial:
            print(f"[POLICY-SKIP] {item_id} status={status} sub={item.get('sub_status')} qty={qty}",flush=True)
        return
    body = {"available_quantity": 1}
    if action == "replenish_out_of_stock":
        body["status"] = "active"
    u = requests.put(f"{API}/items/{item_id}", headers=HJ, json=body, timeout=15)
    if u.status_code not in (200, 201):
        raise RuntimeError(f"{item_id}: PUT {u.status_code} {u.text[:300]}")
    updated = u.json()
    print(f"[REPLENISHED] {item_id} qty {qty}->1 status={status}->{updated.get('status')} title={item.get('title','')}", flush=True)

def check(target, initial=False):
    if target.startswith("MLMU"):
        keep_one_user_product(target, initial=initial)
    else:
        if not enforce_real_stock(target, initial=initial):
            return
        keep_one_item(target, initial=initial)

def ensure_catalog_item(source_item_id):
    source_response = requests.get(f"{API}/items/{source_item_id}", headers=H, timeout=15)
    source_response.raise_for_status()
    source = source_response.json()
    if source.get("catalog_listing"):
        print(f"[CATALOG-READY] {source_item_id} already_catalog=true", flush=True)
        return source_item_id
    for relation in source.get("item_relations") or []:
        related_id = relation.get("id")
        if not related_id:
            continue
        related_response = requests.get(f"{API}/items/{related_id}", headers=H, timeout=15)
        if related_response.status_code == 200 and related_response.json().get("catalog_listing"):
            print(f"[CATALOG-READY] {source_item_id}->{related_id}", flush=True)
            return related_id
    product_id = source.get("catalog_product_id")
    if not product_id:
        raise RuntimeError(f"{source_item_id}: no tiene catalog_product_id")
    optin = requests.post(
        f"{API}/items/catalog_listings",
        headers=HJ,
        json={"item_id": source_item_id, "catalog_product_id": product_id},
        timeout=30,
    )
    if optin.status_code not in (200, 201):
        raise RuntimeError(f"{source_item_id}: opt-in {optin.status_code} {optin.text[:500]}")
    catalog_item_id = optin.json().get("id")
    if not catalog_item_id:
        raise RuntimeError(f"{source_item_id}: opt-in sin item_id {optin.text[:500]}")
    print(f"[CATALOG-OPTIN] {source_item_id}->{catalog_item_id} product={product_id}", flush=True)
    return catalog_item_id

def change_price(item_id, current_price, new_price, reason):
    if new_price == current_price:
        return
    response = requests.put(
        f"{API}/items/{item_id}",
        headers=HJ,
        json={"price": new_price},
        timeout=20,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"{item_id}: price PUT {response.status_code} {response.text[:400]}"
        )
    updated_price = response.json().get("price")
    print(
        f"[CATALOG-PRICE] {item_id} {current_price}->{updated_price} "
        f"reason={reason}",
        flush=True,
    )

def external_competitor_prices(product_id):
    response = requests.get(
        f"{API}/products/{product_id}/items",
        headers=H,
        params={"limit": 100},
        timeout=20,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"{product_id}: competitors GET {response.status_code} {response.text[:300]}"
        )
    prices = []
    for result in response.json().get("results") or []:
        if int(result.get("seller_id") or 0) == SELLER_ID:
            continue
        price = result.get("price")
        if price is not None:
            prices.append(float(price))
    return prices

def repair_buybox_sync(item_id):
    now = time.time()
    if now - SYNC_REPAIR_AT.get(item_id, 0) < 600:
        return
    SYNC_REPAIR_AT[item_id] = now
    sync_headers = {**HJ, "x-public": "True"}
    status_response = requests.get(
        f"{API}/public/buybox/sync/{item_id}",
        headers=sync_headers,
        timeout=15,
    )
    status_data = status_response.json() if status_response.status_code == 200 else {}
    if status_data.get("status") == "SYNC":
        print(f"[CATALOG-SYNC] {item_id} already_sync", flush=True)
        return
    repair = requests.post(
        f"{API}/public/buybox/sync",
        headers=sync_headers,
        json={"id": item_id},
        timeout=20,
    )
    if repair.status_code == 200:
        print(f"[CATALOG-SYNC] {item_id} repaired", flush=True)
    else:
        print(
            f"[CATALOG-SYNC-WARN] {item_id} http={repair.status_code} "
            f"body={repair.text[:300]}",
            flush=True,
        )

def manage_catalog_price(item_id, ceiling, initial=False):
    item_response = requests.get(f"{API}/items/{item_id}", headers=H, timeout=15)
    item_response.raise_for_status()
    item = item_response.json()
    if int(item.get("seller_id") or 0) != SELLER_ID:
        raise RuntimeError(f"{item_id}: seller inesperado {item.get('seller_id')}")
    if "dynamic_standard_price" in (item.get("tags") or []):
        if initial:
            print(
                f"[CATALOG-SKIP] {item_id} usa automatización nativa; "
                "precio API protegido",
                flush=True,
            )
        return
    competition_response = requests.get(
        f"{API}/items/{item_id}/price_to_win",
        headers=H,
        params={"siteId": "MLM", "version": "v2"},
        timeout=20,
    )
    if competition_response.status_code >= 500:
        time.sleep(2)
        competition_response = requests.get(
            f"{API}/items/{item_id}/price_to_win",
            headers=H,
            params={"siteId": "MLM", "version": "v2"},
            timeout=20,
        )
    if competition_response.status_code != 200:
        raise RuntimeError(
            f"{item_id}: price_to_win {competition_response.status_code} "
            f"{competition_response.text[:400]}"
        )
    competition = competition_response.json()
    status = competition.get("status")
    current = competition.get("current_price")
    if current is None:
        current = item.get("price")
    if current is None:
        raise RuntimeError(f"{item_id}: no se pudo determinar precio actual")
    current = float(current)
    ceiling = float(ceiling)
    floor = float(PRICE_FLOOR)

    if status in ("competing", "sharing_first_place"):
        WIN_STREAKS[item_id] = 0
        if current <= floor:
            if initial:
                print(
                    f"[CATALOG-FLOOR] {item_id} status={status} price={current} "
                    f"floor={floor} reason={competition.get('reason')}",
                    flush=True,
                )
            return
        new_price = max(floor, current - PRICE_STEP)
        change_price(item_id, current, new_price, f"status={status}")
        return

    if status == "winning":
        WIN_STREAKS[item_id] = WIN_STREAKS.get(item_id, 0) + 1
        if current >= ceiling:
            if initial:
                print(
                    f"[CATALOG-WINNING] {item_id} price={current} ceiling={ceiling}",
                    flush=True,
                )
            return
        if WIN_STREAKS[item_id] < WIN_STREAK_REQUIRED:
            return
        product_id = competition.get("catalog_product_id") or item.get("catalog_product_id")
        competitors = external_competitor_prices(product_id) if product_id else []
        candidate = min(ceiling, current + PRICE_STEP)
        no_competition_above = not competitors
        safe_below_next = bool(competitors) and candidate < min(competitors)
        if no_competition_above or safe_below_next:
            change_price(
                item_id,
                current,
                candidate,
                "winning_no_competitor" if no_competition_above else
                f"winning_next_competitor={min(competitors)}",
            )
            WIN_STREAKS[item_id] = 0
        elif initial:
            print(
                f"[CATALOG-HOLD] {item_id} winning price={current} "
                f"next_competitor={min(competitors) if competitors else None}",
                flush=True,
            )
        return

    WIN_STREAKS[item_id] = 0
    reasons = competition.get("reason") or []
    if "item_not_opted_in" in reasons:
        repair_buybox_sync(item_id)
    if initial or status not in ("listed", "not_listed"):
        print(
            f"[CATALOG-SKIP] {item_id} status={status} "
            f"reason={reasons}",
            flush=True,
        )

print("=== EDILBERTO: validación inicial de publicaciones autorizadas ===", flush=True)
for target in TARGETS:
    try:
        check(target, initial=True)
    except Exception as exc:
        print(f"[ERROR] {target}: {exc}", flush=True)

print(f"=== EDILBERTO: catálogo y Buy Box enabled={ENABLE_PRICE_WAR} ===", flush=True)
WAR_CATALOG_ITEMS = {}
for source_item_id in (WAR_SOURCE_ITEMS if ENABLE_PRICE_WAR else []):
    try:
        catalog_item_id = ensure_catalog_item(source_item_id)
        WAR_CATALOG_ITEMS[source_item_id] = catalog_item_id
        manage_catalog_price(
            catalog_item_id,
            PRICE_CEILINGS[source_item_id],
            initial=True,
        )
    except Exception as exc:
        print(f"[CATALOG-ERROR] {source_item_id}: {exc}", flush=True)

started = time.time()
cycles = 0
while time.time() - started < DURATION:
    cycles += 1
    cycle_start = time.time()
    for target in TARGETS:
        try:
            check(target)
        except Exception as exc:
            print(f"[ERROR] {target}: {exc}", flush=True)
    for source_item_id, catalog_item_id in WAR_CATALOG_ITEMS.items():
        try:
            manage_catalog_price(
                catalog_item_id,
                PRICE_CEILINGS[source_item_id],
            )
        except Exception as exc:
            print(f"[CATALOG-ERROR] {source_item_id}: {exc}", flush=True)
    if cycles % 20 == 0:
        print(f"[HEARTBEAT] cycles={cycles} elapsed={int(time.time()-started)}s", flush=True)
    delay = TICK - (time.time() - cycle_start)
    if delay > 0:
        time.sleep(delay)
print(f"=== END cycles={cycles} ===", flush=True)
