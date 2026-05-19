"""
Multi-product Purchase event threshold watcher.
Cada producto en PRODUCTS se evalúa para migrar de ClickOut_Meli → PURCHASE optimization
cuando cruza umbrales: 7d>=25 sales OR 14d>=50 sales.
Itera múltiples sellers (Meli accounts) → un solo pixel Meta.
"""
import os, requests, sys
from datetime import datetime, timezone, timedelta

SELLERS = {
    1668713481: "MELI_REFRESH_TOKEN_USER1668",  # ASVA
    3364413125: "MELI_REFRESH_TOKEN_YC_NEW",    # YC
}

PRODUCTS = [
    {
        "mlm": "MLM5356938548", "name": "Dashcam DVR-3", "seller": 1668713481,
        "current_adset": "120245412226100238", "campaign": "120245364929030238",
        "creatives": ["1354381413244933", "1709096793618366", "1343067704408470"]
    },
    {
        "mlm": "MLM2940664057", "name": "Redmi Buds 4 Lite", "seller": 3364413125,
        "current_adset": "120245413762160238", "campaign": "120245413757980238",
        "creatives": ["1465424488963019", "1689643888842798", "1287935986778987"]
    },
    {
        "mlm": "MLM2940986501", "name": "Secadora ASVA", "seller": 1668713481,
        "current_adset": "120245394392190238", "campaign": "120245394293630238",
        "creatives": []
    },
    {
        "mlm": "MLM2886136351", "name": "Bocina 35W Morado", "seller": 1668713481,
        "current_adset": "120245312737330238", "campaign": "120245220932750238",
        "creatives": []
    },
]

THRESHOLD_7D, THRESHOLD_14D = 25, 50

def get_token(token_env):
    rt = os.environ.get(token_env)
    if not rt: return None
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt
    }, timeout=20).json()
    return r.get("access_token")

# Cache tokens por seller
token_cache = {}
def seller_headers(seller_id):
    if seller_id not in token_cache:
        token_cache[seller_id] = get_token(SELLERS[seller_id])
    tok = token_cache[seller_id]
    if not tok: return None
    return {"Authorization": f"Bearer {tok}"}

def count_paid_orders(mlm, seller_id, hours):
    h = seller_headers(seller_id)
    if not h: return -1
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    total = 0; offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search", params={
            "seller": seller_id, "order.status":"paid",
            "order.date_created.from": since,
            "limit":50, "offset":offset, "sort":"date_desc"
        }, headers=h, timeout=20)
        if r.status_code != 200: print(f"  ERR seller {seller_id}: {r.status_code}"); return -1
        j = r.json()
        for o in j.get("results", []):
            for it in (o.get("order_items") or []):
                if (it.get("item") or {}).get("id") == mlm: total += 1; break
        n = len(j.get("results", []))
        if n < 50 or offset >= j.get("paging",{}).get("total",0): break
        offset += 50
    return total

now = datetime.now(timezone.utc)
print(f"=== Products Threshold Watch @ {now.isoformat()[:19]}Z ===")
print(f"Thresholds: 7d>={THRESHOLD_7D} | 14d>={THRESHOLD_14D}\n")

ready_products = []
for p in PRODUCTS:
    c7  = count_paid_orders(p["mlm"], p["seller"], 168)
    c14 = count_paid_orders(p["mlm"], p["seller"], 336)
    ready = (c7 >= THRESHOLD_7D) or (c14 >= THRESHOLD_14D)
    flag = "🚨 READY" if ready else "  pending"
    gap7  = max(0, THRESHOLD_7D - c7)  if c7 >= 0 else "?"
    gap14 = max(0, THRESHOLD_14D - c14) if c14 >= 0 else "?"
    print(f"  {flag} | {p['name']:25} ({p['mlm']}) | 7d={c7:>3} (gap {gap7}) | 14d={c14:>3} (gap {gap14})")
    if ready: ready_products.append({**p, "c7": c7, "c14": c14})

print()
if ready_products:
    print("STATUS: READY_TO_SWITCH_TO_PURCHASE")
    for r in ready_products:
        print(f"\nProduct ready: {r['name']} ({r['mlm']})")
        print(f"  7d sales: {r['c7']} | 14d sales: {r['c14']}")
        print(f"  Action: pause adset {r['current_adset']}, clone with PURCHASE optimization in campaign {r['campaign']}")
        print(f"  Reuse creative_ids: {','.join(r['creatives']) if r['creatives'] else '(adset has no V2 creatives, build from scratch)'}")
else:
    print("STATUS: NOT_READY_ANY")
    print("All products below thresholds. Continue monitoring.")
