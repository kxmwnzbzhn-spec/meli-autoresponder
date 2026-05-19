"""Cuenta rápida Wilbert por substatus. Sin PDFs."""
import os, requests, time
from datetime import datetime, timedelta, timezone
from collections import Counter

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_WILBERT"]

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
at=r["access_token"]
H={"Authorization":f"Bearer {at}"}

me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
uid=me["id"]
NOW=datetime.now(timezone.utc)
START=NOW-timedelta(days=60)
print(f"=== Wilbert ({me.get('nickname')}) — ventana {START.date()} → {NOW.date()} ===")
print(f"Hora corrida: {NOW.isoformat()}")

orders=[]; offset=0
while True:
    r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,timeout=20,
        params={"seller":uid,"order.status":"paid",
                "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":offset}).json()
    res=r.get("results",[])
    if not res: break
    orders.extend(res); offset+=len(res)
    if offset>=r.get("paging",{}).get("total",0): break
sids=set((o.get("shipping") or {}).get("id") for o in orders if (o.get("shipping") or {}).get("id"))
print(f"shipping ids: {len(sids)}")

sub=Counter()
for sid in sids:
    try:
        sh=requests.get(f"https://api.mercadolibre.com/shipments/{sid}",headers=H,timeout=10).json()
        sub[(sh.get("status"), sh.get("substatus") or "(none)")] += 1
        time.sleep(0.03)
    except: pass

print(f"\n=== Distribución status/substatus ===")
total_pend = 0
for (st,sb),n in sub.most_common():
    flag = ""
    if st=="ready_to_ship" and sb in ("printed","ready_to_print"):
        total_pend += n; flag=" ← PENDIENTE"
    print(f"  {n:4} {st}/{sb}{flag}")
print(f"\n*** TOTAL PENDIENTES (ready_to_print + printed): {total_pend} ***")
rtp = sub.get(("ready_to_ship","ready_to_print"),0)
pr  = sub.get(("ready_to_ship","printed"),0)
print(f"   ready_to_print (por imprimir): {rtp}")
print(f"   printed (listas para enviar):  {pr}")
