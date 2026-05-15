"""
Meli Orders → Meta CAPI Purchase event post-back
Scope: SOLO Wilbert (seller_id 3367276814)
Whitelist: solo items definidos abajo (no toca otros productos)
"""
import os, requests, json, hashlib, time, sys
from datetime import datetime, timedelta, timezone

API_MELI = "https://api.mercadolibre.com"
META_GRAPH = "https://graph.facebook.com/v21.0"

# === WHITELIST de items que generan Purchase event a Meta ===
# Solo items que estamos promoviendo con paid traffic
WHITELIST_ITEMS = {
    "MLM2932676401": {
        "name": "Bocina Bluetooth 30W IP67 Acabado Espejo Bass Pro",
        "category": "SPK30W_ESPEJO_V1"
    }
}

EXPECTED_SELLER_ID = 3367276814   # Wilbert only
PIXEL_ID = "1520455545762550"     # Asva E
LOOKBACK_HOURS = 6                # Pull orders de la última 1h (cron 5min sobreposo)


def meli_token():
    r = requests.post(f"{API_MELI}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID"],
        "client_secret": os.environ["MELI_APP_SECRET"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_WILBERT"]
    }, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]


def sha256_hash(value):
    if not value: return None
    return hashlib.sha256(str(value).lower().strip().encode()).hexdigest()


def main():
    capi_token = os.environ.get("META_CAPI_ACCESS_TOKEN")
    if not capi_token:
        print("WARN: META_CAPI_ACCESS_TOKEN no esta seteado, abortando.")
        sys.exit(0)  # exit 0 para no marcar workflow rojo

    test_code = os.environ.get("META_TEST_EVENT_CODE", "")

    tok = meli_token()
    h = {"Authorization": f"Bearer {tok}"}

    since = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    print(f"=== Meta CAPI Post-back run | since={since} | whitelist={list(WHITELIST_ITEMS.keys())} ===")

    # Pull paid orders
    all_orders = []
    offset = 0
    while True:
        r = requests.get(f"{API_MELI}/orders/search", params={
            "seller": EXPECTED_SELLER_ID,
            "order.status": "paid",
            "order.date_created.from": since,
            "limit": 50, "offset": offset, "sort": "date_desc"
        }, headers=h, timeout=20)
        if r.status_code != 200:
            print(f"ERR Meli orders: {r.status_code} {r.text[:200]}")
            sys.exit(1)
        j = r.json()
        results = j.get("results", [])
        all_orders.extend(results)
        if len(results) < 50 or offset >= j.get("paging", {}).get("total", 0): break
        offset += 50

    print(f"Total paid orders pulled: {len(all_orders)}")

    # Filter por whitelist
    target = []
    for o in all_orders:
        for it in o.get("order_items", []):
            iid = (it.get("item") or {}).get("id")
            if iid in WHITELIST_ITEMS:
                target.append((o, it))
                break

    print(f"Orders matching whitelist: {len(target)}")
    if not target:
        print("No relevant orders. Done.")
        return

    # Build Meta CAPI events
    events = []
    for o, item in target:
        iid = item["item"]["id"]
        oid = o["id"]
        ot = o["date_created"]
        dt = datetime.fromisoformat(ot.replace("Z", "+00:00")) if "Z" in ot else datetime.fromisoformat(ot)
        event_time = int(dt.timestamp())

        # Meta rechaza events older than 7 days
        if (datetime.now(timezone.utc).timestamp() - event_time) > 7 * 86400:
            print(f"  skip {oid} too old")
            continue

        buyer = o.get("buyer", {}) or {}
        shipping = o.get("shipping", {}) or {}
        addr = shipping.get("receiver_address", {}) or {}

        user_data = {"country": [sha256_hash("mx")]}
        if buyer.get("id"): user_data["external_id"] = [sha256_hash(str(buyer["id"]))]
        if addr.get("zip_code"): user_data["zp"] = [sha256_hash(addr["zip_code"])]
        city = (addr.get("city") or {}).get("name")
        state = (addr.get("state") or {}).get("name")
        if city: user_data["ct"] = [sha256_hash(city)]
        if state: user_data["st"] = [sha256_hash(state)]

        events.append({
            "event_name": "Purchase",
            "event_time": event_time,
            "event_id": f"meli_order_{oid}",
            "action_source": "physical_store",
            "user_data": user_data,
            "custom_data": {
                "currency": "MXN",
                "value": float(o["total_amount"]),
                "content_ids": [iid],
                "content_name": WHITELIST_ITEMS[iid]["name"],
                "content_type": "product",
                "num_items": int(item.get("quantity", 1)),
                "content_category": WHITELIST_ITEMS[iid]["category"]
            }
        })

    if not events:
        print("No valid events to send. Done.")
        return

    print(f"Sending {len(events)} events to Meta CAPI (pixel {PIXEL_ID})...")
    payload = {"data": events}
    if test_code: payload["test_event_code"] = test_code

    r = requests.post(f"{META_GRAPH}/{PIXEL_ID}/events",
                      params={"access_token": capi_token},
                      json=payload, timeout=30)
    print(f"Meta CAPI HTTP {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text[:500])


if __name__ == "__main__":
    main()
