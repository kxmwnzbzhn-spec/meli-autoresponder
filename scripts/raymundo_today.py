import os, requests
from datetime import datetime, timezone, timedelta

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
UID = me["id"]

# Hoy CDMX = 00:00 -06:00
cdmx_now = datetime.now(timezone.utc) - timedelta(hours=6)
midnight_cdmx = cdmx_now.replace(hour=0, minute=0, second=0, microsecond=0)
date_from = (midnight_cdmx + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

orders, units, gross, paid, cancelled = 0, 0, 0, 0, 0
off = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/orders/search?seller={UID}&order.date_created.from={date_from}&limit=50&offset={off}&sort=date_desc", headers=H, timeout=20).json()
    res = j.get("results", [])
    if not res: break
    for o in res:
        st = o.get("status","")
        orders += 1
        if st == "cancelled": cancelled += 1
        elif st in ("paid","shipped","delivered","handling","ready_to_ship"):
            paid += 1
            gross += float(o.get("total_amount",0) or 0)
            for it in o.get("order_items",[]):
                units += it.get("quantity",0) or 0
    if len(res) < 50: break
    off += 50

print(f"RAYMUNDO HOY ({cdmx_now.strftime('%Y-%m-%d %H:%M')} CDMX):")
print(f"  Total orders:    {orders}")
print(f"  Pagadas/Activas: {paid}")
print(f"  Canceladas:      {cancelled}")
print(f"  Unidades:        {units}")
print(f"  Bruto:           ${gross:,.0f}")
