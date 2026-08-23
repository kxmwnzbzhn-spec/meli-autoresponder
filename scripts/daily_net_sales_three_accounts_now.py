#!/usr/bin/env python3
"""Corte neto en vivo usando pagos aprobados de Mercado Pago."""
import json, os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

API="https://api.mercadolibre.com"
TZ=ZoneInfo("America/Mexico_City")
TIMEOUT=30
ACCOUNTS=[
 ("LUISED",3584846108,"MELI_REFRESH_TOKEN_LUISED","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW","/tmp/luised_rotated_token"),
 ("EDILBERTO",3616975257,"MELI_REFRESH_TOKEN_EDILBERTO","MELI_APP_ID_NEW","MELI_APP_SECRET_NEW","/tmp/edilberto_rotated_token"),
 ("ASVA_E",1668713481,"MELI_REFRESH_TOKEN_ASVA","MELI_APP_ID","MELI_APP_SECRET","/tmp/asva_rotated_token"),
]

def money(v):
 try: return float(v or 0)
 except (TypeError,ValueError): return 0.0

def refresh(row):
 name,seller,secret,app_id,app_secret,path=row
 r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ[app_id],
  "client_secret":os.environ[app_secret],"refresh_token":os.environ[secret],
 },timeout=TIMEOUT)
 r.raise_for_status(); data=r.json()
 with open(path,"w") as f: f.write(data.get("refresh_token",""))
 return data["access_token"]

def get_orders(seller,token,date_from,date_to):
 headers={"Authorization":f"Bearer {token}"}; result=[]; offset=0
 while True:
  r=requests.get(f"{API}/orders/search",headers=headers,params={
   "seller":seller,"order.date_created.from":date_from,
   "order.date_created.to":date_to,"sort":"date_desc","limit":50,"offset":offset,
  },timeout=TIMEOUT)
  r.raise_for_status(); data=r.json(); rows=data.get("results") or []
  result.extend(rows); offset+=len(rows)
  if not rows or offset>=int((data.get("paging") or {}).get("total") or 0): break
 return result

def report(row,date_from,date_to):
 name,seller,*_=row; token=refresh(row); headers={"Authorization":f"Bearer {token}"}
 orders=get_orders(seller,token,date_from,date_to)
 paid=[]; cancelled=0
 for order in orders:
  if order.get("status") in {"cancelled","invalid"}: cancelled+=1; continue
  approved=[p for p in (order.get("payments") or []) if p.get("status")=="approved"]
  if approved or order.get("status") in {"paid","partially_refunded"} or "paid" in set(order.get("tags") or []):
   paid.append((order,approved))

 gross=sum(money(i.get("unit_price"))*int(i.get("quantity") or 0) for o,_ in paid for i in (o.get("order_items") or []))
 sale_fee=sum(money(i.get("sale_fee")) for o,_ in paid for i in (o.get("order_items") or []))
 order_taxes=sum(money((o.get("taxes") or {}).get("amount")) for o,_ in paid)
 net_received=0.0; payment_gross=0.0; fee_types={}; payment_count=0; payment_errors=[]
 seen=set()
 for order,payments in paid:
  for stub in payments:
   pid=stub.get("id")
   if not pid or pid in seen: continue
   seen.add(pid)
   r=requests.get(f"https://api.mercadopago.com/v1/payments/{pid}",headers=headers,timeout=TIMEOUT)
   if r.status_code!=200:
    payment_errors.append({"payment_id":pid,"status":r.status_code}); continue
   p=r.json(); payment_count+=1
   payment_gross+=money(p.get("transaction_amount"))
   net_received+=money((p.get("transaction_details") or {}).get("net_received_amount"))
   for fee in p.get("fee_details") or []:
    typ=fee.get("type") or "unknown"
    fee_types[typ]=fee_types.get(typ,0.0)+money(fee.get("amount"))

 shipping_cost=0.0; shipment_errors=[]; seen_ship=set()
 for order,_ in paid:
  sid=(order.get("shipping") or {}).get("id")
  if not sid or sid in seen_ship: continue
  seen_ship.add(sid)
  r=requests.get(f"{API}/shipments/{sid}/costs",headers=headers,timeout=TIMEOUT)
  if r.status_code!=200:
   shipment_errors.append({"shipment_id":sid,"status":r.status_code}); continue
  costs=r.json()
  matched=False
  for sender in costs.get("senders") or []:
   if str(sender.get("user_id"))==str(seller):
    shipping_cost+=money(sender.get("cost")); matched=True
  if not matched and len(costs.get("senders") or [])==1:
   shipping_cost+=money(costs["senders"][0].get("cost"))

 return {
  "account":name,"seller_id":seller,"paid_orders":len(paid),
  "units":sum(int(i.get("quantity") or 0) for o,_ in paid for i in (o.get("order_items") or [])),
  "gross_items":round(gross,2),"payment_gross":round(payment_gross,2),
  "net_received":round(net_received,2),"sale_fee_from_orders":round(sale_fee,2),
  "order_taxes":round(order_taxes,2),"seller_shipping_cost":round(shipping_cost,2),
  "payment_fees":{k:round(v,2) for k,v in fee_types.items()},
  "payment_count":payment_count,"payment_errors":payment_errors,
  "shipment_errors":shipment_errors,"cancelled_orders":cancelled,
 }

now=datetime.now(TZ); start=datetime.combine(now.date(),time.min,TZ); end=start+timedelta(days=1)
date_from=start.isoformat(timespec="milliseconds"); date_to=end.isoformat(timespec="milliseconds")
accounts=[report(a,date_from,date_to) for a in ACCOUNTS]
out={"date":str(now.date()),"generated_at":now.isoformat(),"accounts":accounts,
 "combined":{
  "paid_orders":sum(a["paid_orders"] for a in accounts),
  "units":sum(a["units"] for a in accounts),
  "gross_items":round(sum(a["gross_items"] for a in accounts),2),
  "net_received":round(sum(a["net_received"] for a in accounts),2),
  "sale_fee_from_orders":round(sum(a["sale_fee_from_orders"] for a in accounts),2),
  "order_taxes":round(sum(a["order_taxes"] for a in accounts),2),
  "seller_shipping_cost":round(sum(a["seller_shipping_cost"] for a in accounts),2),
  "payment_fees":{},
 }}
for a in accounts:
 for k,v in a["payment_fees"].items():
  out["combined"]["payment_fees"][k]=round(out["combined"]["payment_fees"].get(k,0)+v,2)
print("THREE_NET_SALES="+json.dumps(out,ensure_ascii=False),flush=True)
