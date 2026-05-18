"""
Dashcam DVR-3 Purchase event threshold watcher.
Runs daily at 14:00 UTC (8am CDMX). Counts dashcam Meli sales last 7d/14d.
Threshold to migrate optimization from ClickOut_Meli → PURCHASE:
  - last 7d >= 25 sales, OR
  - last 14d >= 50 sales
Output prints structured status that scheduled task reads.
"""
import os, requests, json, sys
from datetime import datetime, timezone, timedelta

DASHCAM_MLM = "MLM5356938548"
SELLER_ID = 1668713481
THRESHOLD_7D = 25
THRESHOLD_14D = 50

tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}

now = datetime.now(timezone.utc)

def count_paid_orders(item_id, hours):
    since = (now - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
    total = 0
    offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search", params={
            "seller": SELLER_ID, "order.status": "paid",
            "order.date_created.from": since,
            "limit": 50, "offset": offset, "sort": "date_desc"
        }, headers=h, timeout=20)
        if r.status_code != 200:
            print(f"ERR fetching orders: {r.status_code}"); sys.exit(1)
        j = r.json()
        for o in j.get("results", []):
            for item in o.get("order_items", []) or []:
                iid = (item.get("item") or {}).get("id") or item.get("id")
                if iid == item_id:
                    total += 1; break
        results_len = len(j.get("results", []))
        if results_len < 50 or offset >= j.get("paging", {}).get("total", 0): break
        offset += 50
    return total

c7  = count_paid_orders(DASHCAM_MLM, 168)
c14 = count_paid_orders(DASHCAM_MLM, 336)

print(f"=== Dashcam Purchase Threshold Watch @ {now.isoformat()[:19]}Z ===")
print(f"Dashcam (MLM5356938548) paid sales: 7d={c7} | 14d={c14}")
print(f"Thresholds: 7d>={THRESHOLD_7D} | 14d>={THRESHOLD_14D}")

ready = (c7 >= THRESHOLD_7D) or (c14 >= THRESHOLD_14D)
if ready:
    print()
    print("STATUS: READY_TO_SWITCH_TO_PURCHASE")
    print(f"REASON: 7d={c7} (need {THRESHOLD_7D}) | 14d={c14} (need {THRESHOLD_14D})")
    print()
    print("Next action: pause current ClickOut adset (120245412226100238)")
    print("Create new adset with promoted_object={pixel_id:'1520455545762550',custom_event_type:'PURCHASE'}")
    print("Reuse creative_ids: 1354381413244933, 1709096793618366, 1343067704408470")
else:
    print()
    print("STATUS: NOT_READY")
    print(f"GAP: 7d gap={max(0,THRESHOLD_7D-c7)} | 14d gap={max(0,THRESHOLD_14D-c14)}")
