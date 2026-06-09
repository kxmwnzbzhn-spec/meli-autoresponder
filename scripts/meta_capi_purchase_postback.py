"""
Meli Orders -> Meta CAPI Purchase post-back - MODO ALL-SALES con dual-pixel routing.

Routing por producto:
- ELITE_PRODUCTS (boxers + perfumes) -> pixel Elite Market 2952595904932530 con ELITE_TOKEN
- Resto -> pixel Sonix 1520455545762550 con CAPI_TOKEN default

Razon: Boxers + perfumes corren bajo Business Manager Elite Market, otros productos bajo Sonix.
Mantener atribucion separada permite training audiences distintos por marca.
"""
import os, requests, json, hashlib, sys
from datetime import datetime, timedelta, timezone
import meli_token

API_MELI = "https://api.mercadolibre.com"
META_GRAPH = "https://graph.facebook.com/v21.0"

# === DUAL PIXEL CONFIG ===
SONIX_PIXEL_ID = "1520455545762550"
ELITE_PIXEL_ID = "2952595904932530"
ELITE_PRODUCTS = {
    "MLM2976325463", "MLM-2976325463",   # Boxers 3-pack Adrian
    "MLM2996229227", "MLM-2996229227",   # Perfume 1M Gold
}

LOOKBACK_HOURS = 168

SELLERS = [
    {"id": 1668713481, "name": "ASVA",    "token_env": "MELI_REFRESH_TOKEN_USER1668"},
    {"id": 3364413125, "name": "YC",      "token_env": "MELI_REFRESH_TOKEN_YC_NEW"},
    {"id": 3367276814, "name": "WILBERT", "token_env": "MELI_REFRESH_TOKEN_WILBERT"},
    {"id": 3417664339, "name": "ADRIAN",  "token_env": "MELI_REFRESH_TOKEN_ADRIAN"},
]

WHITELIST_ITEMS = {
    "MLM2886030837": {"name": "Bocina Bluetooth 35w Rojo",        "category": "SPK35W_ROJO_V1"},
    "MLM2886136351": {"name": "Bocina Bluetooth 35w Morado",      "category": "SPK35W_MORADO_V1"},
    "MLM2940986501": {"name": "Secadora ASVA Ionica Motor Digital","category": "SECADORA_ASVA_V1"},
    "MLM5356938548": {"name": "Dashcam ASVA DVR-3",                "category": "DASHCAM_DVR3_V1"},
    "MLM2940664057": {"name": "Audifonos Bluetooth In-Ear Negro", "category": "AUDIFONOS_BT_V1"},
    "MLM5346655686": {"name": "Bocina Bluetooth Portatil Go4 IP67","category": "SPK_GO4_V1"},
    "MLM2976325463": {"name": "Pack 3 Boxers Premium Hombre",      "category": "APPAREL_BOXERS_V1"},
    "MLM2996229227": {"name": "Perfume Gold Premium 100ml",        "category": "PERFUME_GOLD_V1"},
}

PERFUME_BLACKLIST = {
    "MLM4436177528",  # Oud Cherry (TAL)
    "MLM5374718702",  # Dark Oud Cacao (TAL)
}

ITEM_TO_LANDING = {
    "MLM2886136351": "https://sonixmx.com.mx/bocina-30w-espejo/",
    "MLMU3924350212": "https://sonixmx.com.mx/bocina-30w-espejo/",
    "MLM2943284461": "https://sonixmx.com.mx/dashcam-dvr3/",
    "MLM5356938548": "https://sonixmx.com.mx/dashcam-dvr3/",
    "MLMU3986495886": "https://sonixmx.com.mx/dashcam-dvr3/",
    "MLM2952660425": "https://sonixmx.com.mx/audifonos-buds2/",
    "MLM2952545353": "https://sonixmx.com.mx/audifonos-buds2/",
    "MLM-2958319761": "https://sonixmx.com.mx/bocina-go4/",
    "MLM2958319761": "https://sonixmx.com.mx/bocina-go4/",
    "MLM2940664057": "https://sonixmx.com.mx/audifonos-bt/",
    "MLM2940986501": "https://sonixmx.com.mx/secadora-asva/",
    "MLM2976325463": "https://sonixmx.com.mx/boxers-3pack/",
    "MLM-2976325463": "https://sonixmx.com.mx/boxers-3pack/",
    "MLM2996229227": "https://sonixmx.com.mx/perfume-1m-gold/",
    "MLM-2996229227": "https://sonixmx.com.mx/perfume-1m-gold/",
}
DEFAULT_LANDING = "https://sonixmx.com.mx/"


def get_meli_token(token_env):
    rt = os.environ.get(token_env)
    if not rt:
        print(f"WARN: {token_env} not set, skipping"); return None
    r = meli_token.refresh(rt)
    if r.status_code != 200:
        print(f"ERR refresh {token_env}: {r.status_code} {r.text[:200]}"); return None
    return r.json()["access_token"]

def sha256_hash(value):
    if not value: return None
    return hashlib.sha256(str(value).lower().strip().encode()).hexdigest()

def collect_events_for_seller(seller, since):
    tok = get_meli_token(seller["token_env"])
    if not tok: return []
    h = {"Authorization": f"Bearer {tok}"}
    seller_id = seller["id"]
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

    events_sonix = []
    events_elite = []
    items_in_whitelist = 0
    items_other = 0
    items_elite = 0
    for o in all_orders:
        oid = o["id"]; ot = o["date_created"]
        dt = datetime.fromisoformat(ot.replace("Z", "+00:00")) if "Z" in ot else datetime.fromisoformat(ot)
        event_time = int(dt.timestamp())
        if (datetime.now(timezone.utc).timestamp() - event_time) > 7 * 86400: continue

        items = o.get("order_items", []) or []
        if not items: continue
        first = items[0]
        iid = (first.get("item") or {}).get("id") or "UNKNOWN"
        title = ((first.get("item") or {}).get("title") or "")[:80]

        if iid in PERFUME_BLACKLIST:
            continue

        if iid in WHITELIST_ITEMS:
            meta = WHITELIST_ITEMS[iid]
            content_name = meta["name"]
            content_category = meta["category"]
            items_in_whitelist += 1
        else:
            content_name = title or f"Meli {iid}"
            content_category = "OTHER"
            items_other += 1

        buyer = o.get("buyer", {}) or {}
        addr = (o.get("shipping", {}) or {}).get("receiver_address", {}) or {}
        ud = {"country": [sha256_hash("mx")]}
        if buyer.get("id"): ud["external_id"] = [sha256_hash(str(buyer["id"]))]
        if addr.get("zip_code"): ud["zp"] = [sha256_hash(addr["zip_code"])]
        city = (addr.get("city") or {}).get("name")
        state = (addr.get("state") or {}).get("name")
        if city: ud["ct"] = [sha256_hash(city)]
        if state: ud["st"] = [sha256_hash(state)]

        total_qty = sum(int(it.get("quantity", 1)) for it in items)
        event_source_url = ITEM_TO_LANDING.get(iid, DEFAULT_LANDING)
        event = {
            "event_name": "Purchase", "event_time": event_time,
            "event_id": f"meli_order_{oid}",
            "action_source": "website",
            "event_source_url": event_source_url,
            "user_data": ud,
            "custom_data": {
                "currency": "MXN", "value": float(o["total_amount"]),
                "content_ids": [iid], "content_name": content_name,
                "content_type": "product", "num_items": total_qty,
                "content_category": content_category,
                "order_id": str(oid)
            }
        }

        # Route to ELITE if product is in ELITE_PRODUCTS, else SONIX (default)
        if iid in ELITE_PRODUCTS:
            events_elite.append(event)
            items_elite += 1
        else:
            events_sonix.append(event)

    print(f"  [{seller['name']}] events: sonix={len(events_sonix)} elite={len(events_elite)} (whitelist={items_in_whitelist}, other={items_other}, elite_routed={items_elite})")
    return events_sonix, events_elite

def chunk(lst, n):
    for i in range(0, len(lst), n): yield lst[i:i+n]

def send_to_pixel(events, pixel_id, token, label, test_code=""):
    if not events:
        print(f"  [{label}] no events to send")
        return 0
    print(f"  [{label}] Total events: {len(events)}")
    success = 0
    for batch in chunk(events, 500):
        payload = {"data": batch}
        if test_code: payload["test_event_code"] = test_code
        r = requests.post(f"{META_GRAPH}/{pixel_id}/events",
                          params={"access_token": token}, json=payload, timeout=30)
        print(f"    batch {len(batch)} -> HTTP {r.status_code}")
        if r.status_code == 200:
            success += 1
            try: print(f"      events_received: {r.json().get('events_received','?')}")
            except: pass
        else:
            print(f"      err: {r.text[:300]}")
    return success

def main():
    sonix_token = os.environ.get("META_CAPI_ACCESS_TOKEN")
    elite_token = os.environ.get("META_CAPI_ACCESS_TOKEN_ELITE")
    if not sonix_token: print("ERR: META_CAPI_ACCESS_TOKEN missing"); sys.exit(0)
    if not elite_token: print("WARN: META_CAPI_ACCESS_TOKEN_ELITE missing - elite events will be skipped")
    test_code = os.environ.get("META_TEST_EVENT_CODE", "")

    since = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    print(f"=== DUAL-PIXEL CAPI post-back | since={since} ===")
    print(f"  SONIX pixel: {SONIX_PIXEL_ID}")
    print(f"  ELITE pixel: {ELITE_PIXEL_ID}")
    print(f"  ELITE_PRODUCTS: {sorted(ELITE_PRODUCTS)}")
    print(f"Sellers in scope: {[s['name'] for s in SELLERS]}\n")

    all_sonix = []
    all_elite = []
    for seller in SELLERS:
        print(f"--- Seller: {seller['name']} ({seller['id']}) ---")
        sonix_evs, elite_evs = collect_events_for_seller(seller, since)
        all_sonix.extend(sonix_evs)
        all_elite.extend(elite_evs)

    print(f"\nTotals: sonix={len(all_sonix)} elite={len(all_elite)}")
    s_batches = send_to_pixel(all_sonix, SONIX_PIXEL_ID, sonix_token, "SONIX", test_code)
    e_batches = 0
    if elite_token:
        e_batches = send_to_pixel(all_elite, ELITE_PIXEL_ID, elite_token, "ELITE", test_code)
    print(f"\nDone. Sonix batches success: {s_batches} | Elite batches success: {e_batches}")

if __name__ == "__main__":
    main()
