"""Ver fechas en shipments ready_to_ship/printed para entender filtro 'hoy'."""
import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID = me["id"]

print(f"Hoy CDMX: {(datetime.now(timezone.utc) - timedelta(hours=6)).strftime('%Y-%m-%d')}\n")

date_from = (datetime.now(timezone.utc) - timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
offset=0; printed_n=0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",headers=H,timeout=20).json()
    res = rr.get("results",[])
    if not res: break
    for o in res:
        sh = o.get("shipping",{}) or {}
        sh_id = sh.get("id")
        if not sh_id: continue
        sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
        if sd.get("status") != "ready_to_ship": continue
        if sd.get("substatus") != "printed": continue
        printed_n += 1
        if printed_n <= 5:
            print(f"=== Shipment {sh_id} (substatus={sd.get('substatus')}) ===")
            print(f"  date_created: {sd.get('date_created')}")
            print(f"  date_first_printed: {sd.get('date_first_printed')}")
            print(f"  lead_time keys: {list((sd.get('lead_time') or {}).keys())}")
            lt = sd.get('lead_time') or {}
            for k,v in lt.items():
                print(f"    lead_time.{k}: {v}")
            print()
    offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
print(f"Total printed (Raymundo): {printed_n}")
