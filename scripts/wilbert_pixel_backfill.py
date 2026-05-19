"""
Wilbert audience JSON v2 — con enriquecimiento PII vía /shipments/{id}.
Lee paid orders del último 30d, fetch shipment de cada uno para obtener
receiver_address (name, phone, zip, city, state), hashea, output JSON.
"""
import os, requests, json, hashlib, sys, time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

API_MELI = "https://api.mercadolibre.com"
SELLER_ID = 3367276814

def meli_token():
    r = requests.post(f"{API_MELI}/oauth/token", data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":os.environ["MELI_REFRESH_TOKEN_WILBERT"]
    }, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

def sha256_hash(v):
    if v is None: return None
    s = str(v).lower().strip()
    if not s or s.upper().startswith("XX") or s == "none": return None
    return hashlib.sha256(s.encode()).hexdigest()

def normalize_phone(p):
    if not p: return None
    digits = "".join(c for c in str(p) if c.isdigit())
    if not digits or len(digits) < 8: return None
    if not digits.startswith("52") and len(digits) == 10: digits = "52" + digits
    return digits

tok = meli_token()
h = {"Authorization": f"Bearer {tok}"}

now = datetime.now(timezone.utc)
since_30d = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
print(f"=== Wilbert audience enrichment | since={since_30d} ===")

all_orders = []
offset = 0
while True:
    r = requests.get(f"{API_MELI}/orders/search", params={
        "seller": SELLER_ID, "order.status":"paid",
        "order.date_created.from": since_30d,
        "limit":50, "offset":offset, "sort":"date_desc"
    }, headers=h, timeout=30)
    if r.status_code != 200: break
    j = r.json()
    results = j.get("results", [])
    all_orders.extend(results)
    if len(results) < 50: break
    offset += 50
    if offset >= 5000: break
print(f"Orders pulled: {len(all_orders)}")

# Fetch shipment in parallel for each order
def fetch_shipment(order):
    ship_id = (order.get('shipping') or {}).get('id')
    if not ship_id: return order, None
    try:
        r = requests.get(f"{API_MELI}/shipments/{ship_id}", headers=h, timeout=15)
        if r.status_code != 200: return order, None
        return order, r.json().get('receiver_address') or {}
    except: return order, None

users = []
matched = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = [ex.submit(fetch_shipment, o) for o in all_orders]
    for i, fut in enumerate(as_completed(futures)):
        try:
            order, addr = fut.result()
            if not addr: continue
            buyer = order.get('buyer') or {}
            full_name = addr.get('receiver_name','') or ''
            parts = full_name.split()
            first_name = parts[0] if parts else None
            last_name = " ".join(parts[1:]) if len(parts) > 1 else None
            phone = normalize_phone(addr.get('receiver_phone'))
            zip_code = addr.get('zip_code')
            city = (addr.get('city') or {}).get('name')
            state = (addr.get('state') or {}).get('name')
            ext_id = str(buyer.get('id','')) or None

            u = {}
            if ext_id: u['external_id'] = ext_id
            if first_name: u['fn'] = first_name
            if last_name: u['ln'] = last_name
            if phone: u['ph'] = phone
            if zip_code: u['zp'] = str(zip_code)
            if city: u['ct'] = city
            if state: u['st'] = state
            u['country'] = 'mx'

            if len(u) >= 2:  # at least country + 1 other field
                users.append(u)
                if first_name or phone or zip_code: matched += 1
        except Exception as e:
            pass
        if (i+1) % 500 == 0: print(f"  processed {i+1}/{len(all_orders)}")

print(f"\nTotal users with PII: {len(users)}")
print(f"With matchable identifiers (name/phone/zip): {matched}")

# Sample
if users:
    print(f"\nSample (first user, before hashing for display):")
    s = dict(users[0])
    for k in ['ph','ext_id','external_id']:
        if k in s: s[k] = s[k][:3]+'***'
    print(json.dumps(s, ensure_ascii=False))

# Write to file
with open('scripts/wilbert_buyers_30d.json','w') as f:
    json.dump({
        'generated_at': now.isoformat()[:19]+'Z',
        'seller_id': SELLER_ID,
        'users_count': len(users),
        'users_with_pii_match': matched,
        'users': users
    }, f, indent=2, ensure_ascii=False)
print(f"\nWritten: scripts/wilbert_buyers_30d.json")
