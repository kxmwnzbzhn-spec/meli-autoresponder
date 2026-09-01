"""List order IDs (venta IDs) for Jorge Luis where shipment is ready_to_ship/printed
(status UI: Listas para enviar)."""
import os, sys, time, requests
from datetime import datetime, timedelta, timezone

RT = os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"]
APP_ID = os.environ.get("MELI_APP_ID_NEW") or os.environ["MELI_APP_ID"]
APP_SECRET = os.environ.get("MELI_APP_SECRET_NEW") or os.environ["MELI_APP_SECRET"]

def refresh(a, s):
    return requests.post("https://api.mercadolibre.com/oauth/token",
        data={"grant_type":"refresh_token","client_id":a,"client_secret":s,"refresh_token":RT},
        timeout=25).json()

j = refresh(APP_ID, APP_SECRET)
if not j.get("access_token"):
    j = refresh(os.environ["MELI_APP_ID"], os.environ["MELI_APP_SECRET"])
AT = j["access_token"]
H = {"Authorization":f"Bearer {AT}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
UID = me.get("id")
print(f"[auth] {me.get('nickname')} uid={UID}")

NOW = datetime.now(timezone.utc); START = NOW - timedelta(days=90)
orders=[]; off=0
while True:
    r = requests.get("https://api.mercadolibre.com/orders/search", headers=H, timeout=20,
        params={"seller":UID,"order.status":"paid",
                "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":off}).json()
    res = r.get("results",[])
    if not res: break
    orders.extend(res); off += len(res)
    if off >= r.get("paging",{}).get("total",0): break
print(f"[scan] orders={len(orders)}")

# Agrupa por shipping.id
sh_orders = {}
for o in orders:
    sid = (o.get("shipping") or {}).get("id")
    if sid: sh_orders.setdefault(sid,[]).append(o)

# Para cada shipment, verifica si es ready_to_ship/printed
matching_order_ids = []
for sid, orlist in sh_orders.items():
    try:
        sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10).json()
        if sh.get("status") == "ready_to_ship" and sh.get("substatus") == "printed":
            for o in orlist:
                matching_order_ids.append(str(o.get("id")))
        time.sleep(0.02)
    except Exception as e:
        pass

matching_order_ids = sorted(set(matching_order_ids))
print(f"\n===== ORDER IDs (ventas) en 'Listas para enviar' — Jorge Luis =====")
print(f"total: {len(matching_order_ids)}\n")
for oid in matching_order_ids:
    print(oid)
