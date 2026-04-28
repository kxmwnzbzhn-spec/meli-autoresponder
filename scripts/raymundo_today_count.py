import os, requests
from datetime import datetime, timezone, timedelta
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID=me["id"]
midnight=(datetime.now(timezone.utc)-timedelta(hours=6)).replace(hour=0,minute=0,second=0,microsecond=0).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
ords=0; units=0; bruto=0; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={midnight}&limit=50&offset={offset}",headers=H,timeout=20).json()
    res=rr.get("results",[])
    if not res: break
    for o in res:
        if o.get("status") in ("paid","shipped","delivered"):
            ords += 1
            bruto += o.get("total_amount",0) or 0
            for oi in o.get("order_items",[]): units += oi.get("quantity",0)
    offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
now=(datetime.now(timezone.utc)-timedelta(hours=6)).strftime("%H:%M CDMX")
print(f"RAYMUNDO {now}: {ords} órdenes | {units} unidades | bruto ${bruto:,.0f}")
