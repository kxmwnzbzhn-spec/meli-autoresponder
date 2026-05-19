import os, requests
from datetime import datetime, timezone, timedelta

# Probe ventas del 18-may-2026 todo el día (CDMX timezone UTC-6) por todos los productos en whitelist
SELLERS = [
    {"id": 1668713481, "name": "ASVA", "env": "MELI_REFRESH_TOKEN_USER1668"},
    {"id": 3364413125, "name": "YC", "env": "MELI_REFRESH_TOKEN_YC_NEW"},
    {"id": 3367276814, "name": "WILBERT", "env": "MELI_REFRESH_TOKEN_WILBERT"},
]

WHITELIST = {
    "MLM2886030837": ("Bocina 35W Rojo", 199),
    "MLM2886136351": ("Bocina 35W Morado", 199),
    "MLM2940986501": ("Secadora ASVA", 599),
    "MLM5356938548": ("Dashcam DVR-3", 299),
    "MLM2940664057": ("Audifonos Redmi", 299),
    "MLM5346655686": ("Bocina Go4", 299),
}

# Día 18-may-2026 en CDMX (UTC-6): 18-may 00:00 CDMX = 18-may 06:00 UTC
since = "2026-05-18T06:00:00.000-00:00"
until = "2026-05-19T06:00:00.000-00:00"

totals = {mlm: {"count": 0, "revenue": 0.0, "name": meta[0]} for mlm, meta in WHITELIST.items()}

for s in SELLERS:
    rt = os.environ.get(s["env"])
    if not rt: continue
    tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}, timeout=20).json()
    if "access_token" not in tok: continue
    h = {"Authorization": f"Bearer {tok['access_token']}"}
    offset = 0
    seller_pulled = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search", params={
            "seller": s["id"], "order.status":"paid",
            "order.date_created.from": since,
            "order.date_created.to": until,
            "limit":50, "offset":offset, "sort":"date_desc"}, headers=h, timeout=20)
        if r.status_code != 200: break
        j = r.json()
        results = j.get("results", [])
        seller_pulled += len(results)
        for o in results:
            for it in (o.get("order_items") or []):
                iid = (it.get("item") or {}).get("id")
                if iid in totals:
                    qty = int(it.get("quantity", 1))
                    totals[iid]["count"] += qty
                    totals[iid]["revenue"] += float(o.get("total_amount", 0))
                    break
        if len(results) < 50: break
        offset += 50
    print(f"[{s['name']}] pulled {seller_pulled} paid orders 18-may")

print(f"\n=== Ventas 18-mayo-2026 (CDMX) ===")
total_count, total_rev = 0, 0.0
for mlm, d in totals.items():
    if d["count"] > 0:
        print(f"  {d['name']:25} ({mlm})  ventas: {d['count']:>3}  revenue: ${d['revenue']:>10,.2f}")
        total_count += d["count"]
        total_rev += d["revenue"]
print(f"\n  TOTAL:                                          {total_count:>3}  ${total_rev:>10,.2f}")
