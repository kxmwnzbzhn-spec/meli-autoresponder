import os, requests, json
from datetime import datetime, timedelta, timezone

# Token Meli vía refresh
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_WILBERT"]
}, timeout=20).json()["access_token"]

h = {"Authorization": f"Bearer {tok}"}
since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")

# Pull all paid orders last 24h
all_orders = []
offset = 0
while True:
    r = requests.get("https://api.mercadolibre.com/orders/search", params={
        "seller": 3367276814, "order.status": "paid",
        "order.date_created.from": since, "limit": 50, "offset": offset
    }, headers=h, timeout=20).json()
    results = r.get("results", [])
    if not results: break
    all_orders.extend(results)
    if len(results) < 50: break
    offset += 50

print(f"Total paid orders 24h: {len(all_orders)}")

# Filtrar por MLM2932676401
matching = []
for o in all_orders:
    for it in o.get("order_items", []):
        if (it.get("item") or {}).get("id") == "MLM2932676401":
            matching.append({
                "order_id": o["id"],
                "date": o["date_created"],
                "amount": o["total_amount"],
                "buyer_state": (o.get("shipping",{}).get("receiver_address",{}).get("state",{}) or {}).get("name", "?"),
                "buyer_city": (o.get("shipping",{}).get("receiver_address",{}).get("city",{}) or {}).get("name", "?")
            })
            break

print(f"\n>>> Ventas del Listing B (MLM2932676401) en últimas 24h: {len(matching)} <<<")
for m in matching:
    print(f"  ${m['amount']} | {m['date'][:19]} | {m['buyer_city']}, {m['buyer_state']}")

# También revisar listing original
matching_jbl = sum(1 for o in all_orders for it in o.get("order_items",[]) if (it.get("item") or {}).get("id") == "MLM5347886456")
print(f"\nReferencia: Listing JBL $1,999 (MLM5347886456) en mismas 24h: {matching_jbl} ventas")

# Top sellers del día
from collections import Counter
counts = Counter()
revenue = {}
for o in all_orders:
    for it in o.get("order_items", []):
        iid = (it.get("item") or {}).get("id")
        title = (it.get("item") or {}).get("title", "")
        if iid:
            counts[iid] += 1
            revenue[iid] = revenue.get(iid, 0) + o["total_amount"]
print(f"\n=== TOP 5 productos vendidos últimas 24h ===")
for iid, n in counts.most_common(5):
    print(f"  {n:>3}x {iid} (${revenue[iid]:.0f})")
