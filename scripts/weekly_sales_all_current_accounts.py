#!/usr/bin/env python3
"""Corte semanal de todas las cuentas operativas actuales."""
import json, os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

API="https://api.mercadolibre.com"
TZ=ZoneInfo("America/Mexico_City")
TIMEOUT=30
ACCOUNTS=[
 ("ROCIO_ANGEL","MELI_REFRESH_TOKEN_ROCIOANGEL","fixed","2008666770714005","MELI_APP_SECRET"),
 ("LUIS_EDUARDO","MELI_REFRESH_TOKEN_LUISED","env","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW"),
 ("EDILBERTO","MELI_REFRESH_TOKEN_EDILBERTO","env","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW"),
 ("ASVA_E","MELI_REFRESH_TOKEN_ASVA","env","MELI_APP_ID","MELI_APP_SECRET"),
 ("ALE","MELI_REFRESH_TOKEN_ALE","env","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW"),
]

def refresh(row):
 label,secret,mode,appid,appsecret=row
 rt=os.environ.get(secret)
 if not rt: return None,{"account":label,"error":"secret_missing"}
 client_id=appid if mode=="fixed" else os.environ.get(appid)
 client_secret=os.environ.get(appsecret)
 if not client_id or not client_secret:
  return None,{"account":label,"error":"app_credentials_missing"}
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":client_id,"client_secret":client_secret,"refresh_token":rt},timeout=TIMEOUT)
 if r.status_code!=200:
  return None,{"account":label,"error":"refresh_failed","http":r.status_code,"detail":r.text[:160]}
 data=r.json()
 path=f"/tmp/weekly_rotated_{secret}"
 with open(path,"w") as f:f.write(data.get("refresh_token",""))
 return data["access_token"],None

def orders_for(seller,token,date_from,date_to):
 h={"Authorization":f"Bearer {token}"}; out=[]; offset=0
 while True:
  r=requests.get(f"{API}/orders/search",headers=h,params={"seller":seller,"order.date_created.from":date_from,"order.date_created.to":date_to,"sort":"date_asc","limit":50,"offset":offset},timeout=TIMEOUT)
  r.raise_for_status(); data=r.json(); rows=data.get("results") or []
  out.extend(rows); offset+=len(rows)
  if not rows or offset>=int((data.get("paging") or {}).get("total") or 0):break
 return out

now=datetime.now(TZ)
monday=now.date()-timedelta(days=now.weekday())
start=datetime.combine(monday,time.min,TZ)
date_from=start.isoformat(timespec="milliseconds")
date_to=now.isoformat(timespec="milliseconds")
seen_sellers=set(); reports=[]; errors=[]
for row in ACCOUNTS:
 label=row[0]; token,err=refresh(row)
 if err: errors.append(err); continue
 h={"Authorization":f"Bearer {token}"}
 me=requests.get(f"{API}/users/me",headers=h,timeout=TIMEOUT)
 if me.status_code!=200:
  errors.append({"account":label,"error":"users_me_failed","http":me.status_code});continue
 profile=me.json(); seller=int(profile["id"])
 if seller in seen_sellers:
  errors.append({"account":label,"seller_id":seller,"error":"duplicate_seller_skipped"});continue
 seen_sellers.add(seller)
 orders=orders_for(seller,token,date_from,date_to)
 paid=[]; cancelled=[]; pending=[]; products={}
 for order in orders:
  status=order.get("status"); tags=set(order.get("tags") or [])
  approved=any(p.get("status")=="approved" for p in (order.get("payments") or []))
  if status in {"cancelled","invalid"}:cancelled.append(order);continue
  if status in {"paid","partially_refunded"} or "paid" in tags or approved:
   paid.append(order)
   for oi in order.get("order_items") or []:
    item=oi.get("item") or {}; iid=item.get("id") or "SIN_ID"; qty=int(oi.get("quantity") or 0)
    amount=float(oi.get("unit_price") or 0)*qty
    p=products.setdefault(iid,{"item_id":iid,"title":item.get("title") or "","units":0,"amount":0.0})
    p["units"]+=qty;p["amount"]+=amount
  else:pending.append(order)
 for p in products.values():p["amount"]=round(p["amount"],2)
 reports.append({"account":label,"nickname":profile.get("nickname"),"seller_id":seller,"paid_orders":len(paid),"units":sum(p["units"] for p in products.values()),"sales_amount":round(sum(p["amount"] for p in products.values()),2),"cancelled_orders":len(cancelled),"pending_orders":len(pending),"products":sorted(products.values(),key=lambda x:(-x["amount"],x["title"]))})
out={"from":start.isoformat(),"to":now.isoformat(),"timezone":str(TZ),"accounts":reports,"errors":errors,"combined":{"paid_orders":sum(x["paid_orders"] for x in reports),"units":sum(x["units"] for x in reports),"sales_amount":round(sum(x["sales_amount"] for x in reports),2),"cancelled_orders":sum(x["cancelled_orders"] for x in reports),"pending_orders":sum(x["pending_orders"] for x in reports)}}
print("WEEKLY_ALL_ACCOUNTS="+json.dumps(out,ensure_ascii=False),flush=True)
