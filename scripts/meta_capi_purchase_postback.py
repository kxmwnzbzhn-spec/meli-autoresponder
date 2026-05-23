"""
Meli Orders → Meta CAPI Purchase post-back · MODO ALL-SALES.
Manda Purchase event al pixel POR CADA orden paid de cualquier seller en SELLERS,
sin filtrar por whitelist. WHITELIST_ITEMS solo se usa para mapear category amigable;
items fuera de la whitelist se mandan con category="OTHER" pero igual alimentan el pixel.

Razón: más volumen de Purchase events = mejor pixel profile = cold start más rápido
para futuras campañas + atribución modelada más precisa para las activas.
"""
import os, requests, json, hashlib, sys
from datetime import datetime, timedelta, timezone
import meli_token

API_MELI = "https://api.mercadolibre.com"
META_GRAPH = "https://graph.facebook.com/v21.0"
PIXEL_ID = "1520455545762550"
LOOKBACK_HOURS = 24

SELLERS = [
    {"id": 1668713481, "name": "ASVA",    "token_env": "MELI_REFRESH_TOKEN_USER1668"},
    {"id": 3364413125, "name": "YC",      "token_env": "MELI_REFRESH_TOKEN_YC_NEW"},
    {"id": 3367276814, "name": "WILBERT", "token_env": "MELI_REFRESH_TOKEN_WILBERT"},
]

# Solo metadata amigable para items que conocemos.
# Items fuera de esta tabla igual se mandan al pixel, pero con category="OTHER".
WHITELIST_ITEMS = {
    "MLM2886030837": {"name": "Bocina Bluetooth 35w Rojo",        "category": "SPK35W_ROJO_V1"},
    "MLM2886136351": {"name": "Bocina Bluetooth 35w Morado",      "category": "SPK35W_MORADO_V1"},
    "MLM2940986501": {"name": "Secadora ASVA Ionica Motor Digital","category": "SECADORA_ASVA_V1"},
    "MLM5356938548": {"name": "Dashcam ASVA DVR-3",                "category": "DASHCAM_DVR3_V1"},
    "MLM2940664057": {"name": "Audifonos Bluetooth In-Ear Negro", "category": "AUDIFONOS_BT_V1"},
    "MLM5346655686": {"name": "Bocina Bluetooth Portatil Go4 IP67","category": "SPK_GO4_V1"},
}

# PERFUME_BLACKLIST — SKUs TAL que NO van al pixel Sonix.
# Los maneja tal-meli-pipeline al pixel TAL 2062725974505434 (atribución separada).
PERFUME_BLACKLIST = {
    "MLM4436177528",  # Oud Cherry (TAL)
    "MLM5374718702",  # Dark Oud Cacao (TAL)
}

def meli_token(token_env):
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
    tok = meli_token(seller["token_env"])
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

    events = []
    items_in_whitelist = 0
    items_other = 0
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
            continue  # perfume TAL → pixel TAL via tal-meli-pipeline, NO al pixel Sonix

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

        events.append({
            "event_name": "Purchase", "event_time": event_time,
            "event_id": f"meli_order_{oid}", "action_source": "physical_store",
            "user_data": ud,
            "custom_data": {
                "currency": "MXN", "value": float(o["total_amount"]),
                "content_ids": [iid], "content_name": content_name,
                "content_type": "product", "num_items": total_qty,
                "content_category": content_category
            }
        })
    print(f"  [{seller['name']}] events: {len(events)} (whitelist={items_in_whitelist}, other={items_other})")
    return events

def chunk(lst, n):
    for i in range(0, len(lst), n): yield lst[i:i+n]

def main():
    capi_token = os.environ.get("META_CAPI_ACCESS_TOKEN")
    if not capi_token: print("ERR: META_CAPI_ACCESS_TOKEN missing"); sys.exit(0)
    test_code = os.environ.get("META_TEST_EVENT_CODE", "")

    since = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    print(f"=== ALL-SALES CAPI post-back | since={since} | pixel={PIXEL_ID} ===")
    print(f"Sellers in scope: {[s['name'] for s in SELLERS]}\n")

    all_events = []
    for seller in SELLERS:
        print(f"--- Seller: {seller['name']} ({seller['id']}) ---")
        all_events.extend(collect_events_for_seller(seller, since))

    if not all_events:
        print("\nNo events to send. Done."); return

    # Meta CAPI accepts up to 1000 events per request — batch para evitar payload too big
    print(f"\nTotal events to send: {len(all_events)}")
    success_chunks = 0
    for batch in chunk(all_events, 500):
        payload = {"data": batch}
        if test_code: payload["test_event_code"] = test_code
        r = requests.post(f"{META_GRAPH}/{PIXEL_ID}/events",
                          params={"access_token": capi_token}, json=payload, timeout=30)
        print(f"  batch {len(batch)} events → HTTP {r.status_code}")
        if r.status_code == 200:
            success_chunks += 1
            try: print(f"    events_received: {r.json().get('events_received','?')}")
            except: pass
        else:
            print(f"    err: {r.text[:300]}")
    print(f"\nDone. Batches success: {success_chunks}")

if __name__ == "__main__":
    main()
