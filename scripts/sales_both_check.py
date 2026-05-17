import os, requests
from datetime import datetime, timedelta, timezone

tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}

since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
all_o = []; offset = 0
while True:
    r = requests.get(f"https://api.mercadolibre.com/orders/search?seller=1668713481&order.status=paid&order.date_created.from={since}&limit=50&offset={offset}", headers=h, timeout=20).json()
    res = r.get("results", [])
    if not res: break
    all_o.extend(res)
    if len(res) < 50: break
    offset += 50

print(f"=== Ventas paid ASVAELECTRONICS últimas 24h ===\n")
print(f"Total orders: {len(all_o)}\n")

bocina = []
dashcam = []
for o in all_o:
    for it in o.get('order_items', []):
        iid = (it.get('item') or {}).get('id')
        if iid == "MLM2886030837":
            bocina.append({"date": o['date_created'], "amount": o['total_amount']})
            break
        elif iid == "MLM5356938548":
            dashcam.append({"date": o['date_created'], "amount": o['total_amount']})
            break

print(f">>> BOCINA ROJA (MLM2886030837): {len(bocina)} ventas — revenue ${sum(m['amount'] for m in bocina):.0f}")
for m in bocina:
    print(f"    ${m['amount']:.0f} | {m['date'][:19]}")

print(f"\n>>> DASHCAM DVR-3 (MLM5356938548): {len(dashcam)} ventas — revenue ${sum(m['amount'] for m in dashcam):.0f}")
for m in dashcam:
    print(f"    ${m['amount']:.0f} | {m['date'][:19]}")

# Verificar listing dashcam current state
print(f"\n=== Estado actual listings ===")
for mid, label in [("MLM2886030837", "BOCINA ROJA"), ("MLM5356938548", "DASHCAM DVR-3")]:
    r = requests.get(f"https://api.mercadolibre.com/items/{mid}?attributes=id,price,available_quantity,sold_quantity,status,shipping", headers=h, timeout=15).json()
    print(f"  {label}: ${r.get('price')} | stock {r.get('available_quantity')} | sold {r.get('sold_quantity')} | free_ship {r.get('shipping',{}).get('free_shipping')}")
