"""Ver estructura de fechas en shipments ready_to_ship para entender filtro de 'hoy'."""
import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID = me["id"]

cdmx_today = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d")
print(f"Hoy CDMX: {cdmx_today}\n")

# Get sample shipments
date_from = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=10",headers=H,timeout=20).json()
for o in rr.get("results",[])[:3]:
    sh = o.get("shipping",{}) or {}
    sh_id = sh.get("id")
    if not sh_id: continue
    sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
    if sd.get("status") != "ready_to_ship": continue
    print(f"=== Shipment {sh_id} ===")
    print(f"  status: {sd.get('status')} / {sd.get('substatus')}")
    print(f"  date_created: {sd.get('date_created')}")
    print(f"  date_first_printed: {sd.get('date_first_printed')}")
    lt = sd.get("lead_time",{})
    print(f"  lead_time.estimated_handling_limit: {lt.get('estimated_handling_limit')}")
    print(f"  lead_time.estimated_delivery_limit: {lt.get('estimated_delivery_limit')}")
    print(f"  lead_time.estimated_delivery_time: {lt.get('estimated_delivery_time')}")
    print(f"  shipping_option.estimated_handling_limit: {sd.get('shipping_option',{}).get('estimated_handling_limit')}")
    print()
