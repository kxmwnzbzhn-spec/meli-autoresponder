"""
Wilbert 30-day backfill al pixel Meta.
- Pulla últimos 30 días de orders paid del seller WILBERT (3367276814)
- Para órdenes <= 7 días: manda Purchase event al pixel CAPI directo
- Para órdenes 8-30 días: hashea PII del buyer, escribe a wilbert_buyers_30d.json
  → ese JSON se sube a Meta como Custom Audience después
"""
import os, requests, json, hashlib, sys
from datetime import datetime, timedelta, timezone

API_MELI = "https://api.mercadolibre.com"
META_GRAPH = "https://graph.facebook.com/v21.0"
PIXEL_ID = "1520455545762550"
SELLER_ID = 3367276814  # Wilbert
LOOKBACK_DAYS = 30
CAPI_WINDOW_DAYS = 7

def meli_token():
    r = requests.post(f"{API_MELI}/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["MELI_APP_ID"],
        "client_secret": os.environ["MELI_APP_SECRET"],
        "refresh_token": os.environ["MELI_REFRESH_TOKEN_WILBERT"]
    }, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

def sha256_hash(v):
    if not v: return None
    return hashlib.sha256(str(v).lower().strip().encode()).hexdigest()

def normalize_phone(p):
    if not p: return None
    digits = "".join(c for c in str(p) if c.isdigit())
    if not digits: return None
    if not digits.startswith("52") and len(digits) == 10: digits = "52" + digits
    return digits

def main():
    capi_token = os.environ.get("META_CAPI_ACCESS_TOKEN")
    if not capi_token: print("ERR: META_CAPI_ACCESS_TOKEN missing"); sys.exit(1)

    tok = meli_token()
    h = {"Authorization": f"Bearer {tok}"}

    now = datetime.now(timezone.utc)
    since_30d = (now - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    capi_cutoff = (now - timedelta(days=CAPI_WINDOW_DAYS)).timestamp()
    print(f"=== Wilbert Backfill | since={since_30d} | CAPI cutoff: events newer than {CAPI_WINDOW_DAYS}d ===")

    all_orders = []
    offset = 0
    while True:
        r = requests.get(f"{API_MELI}/orders/search", params={
            "seller": SELLER_ID, "order.status": "paid",
            "order.date_created.from": since_30d, "limit": 50, "offset": offset, "sort": "date_desc"
        }, headers=h, timeout=30)
        if r.status_code != 200:
            print(f"ERR orders: {r.status_code}"); break
        j = r.json()
        results = j.get("results", [])
        all_orders.extend(results)
        if len(results) < 50: break
        offset += 50
        if offset >= 5000:  # safety stop
            print("WARN: 5000+ orders, stopping pagination"); break
    print(f"Total paid orders pulled (30d): {len(all_orders)}")

    capi_events = []
    audience_users = []
    skipped = 0

    for o in all_orders:
        oid = o["id"]; ot = o["date_created"]
        dt = datetime.fromisoformat(ot.replace("Z", "+00:00")) if "Z" in ot else datetime.fromisoformat(ot)
        event_time = int(dt.timestamp())

        items = o.get("order_items", []) or []
        if not items: skipped += 1; continue
        first = items[0]
        iid = (first.get("item") or {}).get("id") or "UNKNOWN"
        title = ((first.get("item") or {}).get("title") or "")[:80]

        buyer = o.get("buyer", {}) or {}
        addr = (o.get("shipping", {}) or {}).get("receiver_address", {}) or {}

        # Hash PII para CAPI + Custom Audience
        external_id = sha256_hash(str(buyer["id"])) if buyer.get("id") else None
        first_name = sha256_hash(buyer.get("first_name") or addr.get("receiver_name","").split(" ")[0])
        last_name = sha256_hash(buyer.get("last_name") or " ".join(addr.get("receiver_name","").split(" ")[1:]))
        zip_h = sha256_hash(addr.get("zip_code"))
        city_h = sha256_hash((addr.get("city") or {}).get("name"))
        state_h = sha256_hash((addr.get("state") or {}).get("name"))
        country_h = sha256_hash("mx")
        phone_normalized = normalize_phone(addr.get("receiver_phone"))
        phone_h = sha256_hash(phone_normalized) if phone_normalized else None

        ud = {"country": [country_h]}
        if external_id: ud["external_id"] = [external_id]
        if zip_h: ud["zp"] = [zip_h]
        if city_h: ud["ct"] = [city_h]
        if state_h: ud["st"] = [state_h]
        if first_name: ud["fn"] = [first_name]
        if last_name: ud["ln"] = [last_name]
        if phone_h: ud["ph"] = [phone_h]

        total_qty = sum(int(it.get("quantity", 1)) for it in items)

        # Si está dentro del window CAPI, manda Purchase event
        if event_time >= capi_cutoff:
            capi_events.append({
                "event_name": "Purchase", "event_time": event_time,
                "event_id": f"meli_order_{oid}_backfill", "action_source": "physical_store",
                "user_data": ud,
                "custom_data": {
                    "currency": "MXN", "value": float(o["total_amount"]),
                    "content_ids": [iid], "content_name": title or f"Meli {iid}",
                    "content_type": "product", "num_items": total_qty,
                    "content_category": "WILBERT_BACKFILL_7D"
                }
            })

        # En audience (TODO 30d incluyendo 7d recientes — refuerzo)
        u_audience = {}
        if external_id: u_audience["external_id"] = external_id
        if zip_h: u_audience["zp"] = zip_h
        if city_h: u_audience["ct"] = city_h
        if state_h: u_audience["st"] = state_h
        if first_name: u_audience["fn"] = first_name
        if last_name: u_audience["ln"] = last_name
        if phone_h: u_audience["ph"] = phone_h
        if u_audience: audience_users.append(u_audience)

    print(f"\nCAPI events (<= 7d): {len(capi_events)}")
    print(f"Audience users (30d): {len(audience_users)}")
    print(f"Skipped (no items): {skipped}")

    # Mandar CAPI events en batches de 500
    if capi_events:
        sent = 0
        for i in range(0, len(capi_events), 500):
            batch = capi_events[i:i+500]
            r = requests.post(f"{META_GRAPH}/{PIXEL_ID}/events",
                              params={"access_token": capi_token}, json={"data": batch}, timeout=30)
            if r.status_code == 200:
                sent += len(batch)
                print(f"  batch {len(batch)} → HTTP 200 events_received={r.json().get('events_received','?')}")
            else:
                print(f"  batch {len(batch)} → HTTP {r.status_code} {r.text[:200]}")
        print(f"\nCAPI sent: {sent}/{len(capi_events)}")

    # Guarda audience users a JSON para upload posterior
    out_path = "scripts/wilbert_buyers_30d.json"
    with open(out_path, "w") as f:
        json.dump({
            "generated_at": now.isoformat()[:19] + "Z",
            "seller": "WILBERT",
            "seller_id": SELLER_ID,
            "users_count": len(audience_users),
            "users": audience_users
        }, f, indent=2)
    print(f"\nAudience JSON written: {out_path}")

if __name__ == "__main__":
    main()
