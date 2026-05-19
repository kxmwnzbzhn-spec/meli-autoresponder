"""
Meli Orders → Meta CAPI Purchase post-back (MULTI-SELLER).
Itera sobre N cuentas Meli, todas alimentando el MISMO pixel Meta.
Whitelist por item con seller_id implícito vía SELLERS config.
"""
import os, requests, json, hashlib, sys
from datetime import datetime, timedelta, timezone

API_MELI = "https://api.mercadolibre.com"
META_GRAPH = "https://graph.facebook.com/v21.0"
PIXEL_ID = "1520455545762550"
LOOKBACK_HOURS = 24

# Cada seller: id en Meli + nombre del env var con su refresh_token
SELLERS = [
    {"id": 1668713481, "name": "ASVA",    "token_env": "MELI_REFRESH_TOKEN_USER1668"},
    {"id": 3364413125, "name": "YC",      "token_env": "MELI_REFRESH_TOKEN_YC_NEW"},
    {"id": 3367276814, "name": "WILBERT", "token_env": "MELI_REFRESH_TOKEN_WILBERT"},
]

# Whitelist global: cada item conoce a qué seller pertenece
WHITELIST_ITEMS = {
    "MLM2886030837": {"seller": 1668713481, "name": "Bocina Bluetooth 35w Rojo",        "category": "SPK35W_ROJO_V1"},
    "MLM2886136351": {"seller": 1668713481, "name": "Bocina Bluetooth 35w Morado",      "category": "SPK35W_MORADO_V1"},
    "MLM3545177574": {"seller": 1668713481, "name": "Secadora ASVA Ionica Motor Digital","category": "SECADORA_ASVA_V1"},
    "MLM5356938548": {"seller": 1668713481, "name": "Dashcam ASVA DVR-3",                "category": "DASHCAM_DVR3_V1"},
    "MLM2940664057": {"seller": 3364413125, "name": "Audifonos Bluetooth In-Ear Negro", "category": "AUDIFONOS_BT_V1"},
    "MLM5346655686": {"seller": 3367276814, "name": "Bocina Bluetooth Portatil Go4 IP67",    "category": "SPK_GO4_V1"},
}

def meli_token(token_env):
    rt = os.environ.get(token_env)
    if not rt:
        print(f"WARN: {token_env} not set, skipping this seller"); return None
    r = requests.post(f"{API_MELI}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID"],
        "client_secret": os.environ["MELI_APP_SECRET"],
        "refresh_token": rt
    }, timeout=20)
    if r.status_code != 200:
        print(f"ERR refresh {token_env}: {r.status_code} {r.text[:200]}"); return None
    return r.json()["access_token"]

def sha256_hash(value):
    if not value: return None
    return hashlib.sha256(str(value).lower().strip().encode()).hexdigest()

def collect_events_for_seller(seller, since):
    tok = meli_token(seller["token_env"])
    if not tok: return []
    h = {"Authorization": f"Bearer {tok}"}
    seller_id = seller["id"]
    seller_whitelist = {iid: meta for iid, meta in WHITELIST_ITEMS.items() if meta["seller"] == seller_id}
    if not seller_whitelist:
        print(f"  [{seller['name']}] no items in whitelist, skip"); return []

    all_orders = []
    offset = 0
    while True:
        r = requests.get(f"{API_MELI}/orders/search", params={
            "seller": seller_id, "order.status": "paid",
            "order.date_created.from": since, "limit": 50, "offset": offset, "sort": "date_desc"
        }, headers=h, timeout=20)
        if r.status_code != 200:
            print(f"  [{seller['name']}] ERR orders: {r.status_code}"); break
        j = r.json()
        results = j.get("results", [])
        all_orders.extend(results)
        if len(results) < 50 or offset >= j.get("paging", {}).get("total", 0): break
        offset += 50
    print(f"  [{seller['name']}] orders pulled: {len(all_orders)}")

    target = []
    for o in all_orders:
        for it in o.get("order_items", []):
            iid = (it.get("item") or {}).get("id")
            if iid in seller_whitelist:
                target.append((o, it, iid)); break
    print(f"  [{seller['name']}] orders matching whitelist: {len(target)}")

    events = []
    for o, item, iid in target:
        oid = o["id"]; ot = o["date_created"]
        dt = datetime.fromisoformat(ot.replace("Z", "+00:00")) if "Z" in ot else datetime.fromisoformat(ot)
        event_time = int(dt.timestamp())
        if (datetime.now(timezone.utc).timestamp() - event_time) > 7 * 86400: continue
        buyer = o.get("buyer", {}) or {}
        addr = (o.get("shipping", {}) or {}).get("receiver_address", {}) or {}
        ud = {"country": [sha256_hash("mx")]}
        if buyer.get("id"): ud["external_id"] = [sha256_hash(str(buyer["id"]))]
        if addr.get("zip_code"): ud["zp"] = [sha256_hash(addr["zip_code"])]
        city = (addr.get("city") or {}).get("name")
        state = (addr.get("state") or {}).get("name")
        if city: ud["ct"] = [sha256_hash(city)]
        if state: ud["st"] = [sha256_hash(state)]

        meta = seller_whitelist[iid]
        events.append({
            "event_name": "Purchase", "event_time": event_time,
            "event_id": f"meli_order_{oid}", "action_source": "physical_store",
            "user_data": ud,
            "custom_data": {
                "currency": "MXN", "value": float(o["total_amount"]),
                "content_ids": [iid], "content_name": meta["name"],
                "content_type": "product", "num_items": int(item.get("quantity", 1)),
                "content_category": meta["category"]
            }
        })
    return events

def main():
    capi_token = os.environ.get("META_CAPI_ACCESS_TOKEN")
    if not capi_token: print("ERR: META_CAPI_ACCESS_TOKEN missing"); sys.exit(0)
    test_code = os.environ.get("META_TEST_EVENT_CODE", "")

    since = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    print(f"=== Multi-seller CAPI post-back | since={since} | pixel={PIXEL_ID} ===")
    print(f"Sellers in scope: {[s['name'] for s in SELLERS]}")
    print(f"Whitelist items: {len(WHITELIST_ITEMS)}")

    all_events = []
    for seller in SELLERS:
        print(f"\n--- Seller: {seller['name']} ({seller['id']}) ---")
        all_events.extend(collect_events_for_seller(seller, since))

    if not all_events:
        print("\nNo events to send. Done."); return

    print(f"\nSending {len(all_events)} Purchase events to pixel {PIXEL_ID}...")
    payload = {"data": all_events}
    if test_code: payload["test_event_code"] = test_code
    r = requests.post(f"{META_GRAPH}/{PIXEL_ID}/events",
                      params={"access_token": capi_token}, json=payload, timeout=30)
    print(f"Meta CAPI HTTP {r.status_code}")
    try: print(json.dumps(r.json(), indent=2))
    except: print(r.text[:500])

if __name__ == "__main__":
    main()
