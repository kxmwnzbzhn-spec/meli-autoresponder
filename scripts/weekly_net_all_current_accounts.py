#!/usr/bin/env python3
"""Neto semanal real operativo: bruto menos comisiones, envíos, impuestos y reembolsos."""
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

API="https://api.mercadolibre.com"; TZ=ZoneInfo("America/Mexico_City"); TIMEOUT=30
ACCOUNTS=[
 ("ROCIO_ANGEL","MELI_REFRESH_TOKEN_ROCIOANGEL","fixed","2008666770714005","MELI_APP_SECRET"),
 ("LUIS_EDUARDO","MELI_REFRESH_TOKEN_LUISED","env","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW"),
 ("EDILBERTO","MELI_REFRESH_TOKEN_EDILBERTO","env","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW"),
 ("ASVA_E","MELI_REFRESH_TOKEN_ASVA","env","MELI_APP_ID","MELI_APP_SECRET"),
 ("ALE","MELI_REFRESH_TOKEN_ALE","env","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW"),
]
def val(x):
 try:return float(x or 0)
 except:return 0.0
def refresh(row):
 label,secret,mode,appid,appsecret=row; rt=os.environ.get(secret)
 if not rt:return None,{"account":label,"error":"secret_missing"}
 cid=appid if mode=="fixed" else os.environ.get(appid); cs=os.environ.get(appsecret)
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":cid,"client_secret":cs,"refresh_token":rt},timeout=TIMEOUT)
 if r.status_code!=200:return None,{"account":label,"error":"refresh_failed","http":r.status_code,"detail":r.text[:160]}
 data=r.json()
 with open(f"/tmp/weekly_net_rotated_{secret}","w") as f:f.write(data.get("refresh_token",""))
 return data["access_token"],None
def orders_for(seller,token,start,end):
 h={"Authorization":f"Bearer {token}"}; out=[]; offset=0
 while True:
  r=requests.get(f"{API}/orders/search",headers=h,params={"seller":seller,"order.date_created.from":start,"order.date_created.to":end,"sort":"date_asc","limit":50,"offset":offset},timeout=TIMEOUT)
  r.raise_for_status(); d=r.json(); rows=d.get("results") or [];out.extend(rows);offset+=len(rows)
  if not rows or offset>=int((d.get("paging") or {}).get("total") or 0):break
 return out
def paid(order):
 status=order.get("status"); tags=set(order.get("tags") or [])
 return status not in {"cancelled","invalid"} and (status in {"paid","partially_refunded"} or "paid" in tags or any(p.get("status") in {"approved","refunded","charged_back"} for p in (order.get("payments") or [])))
def shipping_cost(token,seller,sid):
 h={"Authorization":f"Bearer {token}"}
 r=requests.get(f"{API}/shipments/{sid}/costs",headers=h,timeout=TIMEOUT)
 if r.status_code!=200:return sid,0.0,r.status_code
 d=r.json(); senders=d.get("senders") or []; cost=0.0;matched=False
 for x in senders:
  if str(x.get("user_id"))==str(seller):cost+=val(x.get("cost"));matched=True
 if not matched and len(senders)==1:cost+=val(senders[0].get("cost"))
 return sid,cost,200

now=datetime.now(TZ); monday=now.date()-timedelta(days=now.weekday()); start=datetime.combine(monday,time.min,TZ)
start_s=start.isoformat(timespec="milliseconds"); end_s=now.isoformat(timespec="milliseconds")
reports=[];errors=[];seen=set()
for row in ACCOUNTS:
 label=row[0];token,err=refresh(row)
 if err:errors.append(err);continue
 h={"Authorization":f"Bearer {token}"}; me=requests.get(f"{API}/users/me",headers=h,timeout=TIMEOUT)
 if me.status_code!=200:errors.append({"account":label,"error":"users_me_failed","http":me.status_code});continue
 profile=me.json();seller=int(profile["id"])
 if seller in seen:errors.append({"account":label,"error":"duplicate_seller_skipped","seller_id":seller});continue
 seen.add(seller);orders=[o for o in orders_for(seller,token,start_s,end_s) if paid(o)]
 gross=sum(val(i.get("unit_price"))*int(i.get("quantity") or 0) for o in orders for i in (o.get("order_items") or []))
 commissions=sum(val(i.get("sale_fee")) for o in orders for i in (o.get("order_items") or []))
 taxes=sum(val((o.get("taxes") or {}).get("amount")) for o in orders)
 refunds=0.0
 for o in orders:
  for p in o.get("payments") or []:
   refunded=val(p.get("transaction_amount_refunded"))
   if not refunded and p.get("status") in {"refunded","charged_back"}:refunded=val(p.get("transaction_amount"))
   refunds+=refunded
 sids=sorted({(o.get("shipping") or {}).get("id") for o in orders if (o.get("shipping") or {}).get("id")})
 shipping=0.0;ship_errors=[]
 with ThreadPoolExecutor(max_workers=8) as pool:
  futures=[pool.submit(shipping_cost,token,seller,sid) for sid in sids]
  for fut in as_completed(futures):
   sid,cost,http=fut.result();shipping+=cost
   if http!=200:ship_errors.append({"shipment_id":sid,"http":http})
 net=gross-commissions-taxes-refunds-shipping
 reports.append({"account":label,"nickname":profile.get("nickname"),"seller_id":seller,"paid_orders":len(orders),"gross":round(gross,2),"commissions":round(commissions,2),"shipping":round(shipping,2),"taxes":round(taxes,2),"refunds":round(refunds,2),"net":round(net,2),"shipment_errors":ship_errors})
combined={k:round(sum(x[k] for x in reports),2) for k in ("gross","commissions","shipping","taxes","refunds","net")}
combined["paid_orders"]=sum(x["paid_orders"] for x in reports)
out={"from":start.isoformat(),"to":now.isoformat(),"timezone":str(TZ),"accounts":reports,"errors":errors,"combined":combined}
print("WEEKLY_NET_ALL_ACCOUNTS="+json.dumps(out,ensure_ascii=False),flush=True)
