#!/usr/bin/env python3
"""Corte histórico de utilidad compartida de bocinas en ROCIOANGEL."""
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import requests

API="https://api.mercadolibre.com"; TZ=ZoneInfo("America/Mexico_City"); TIMEOUT=30
APP_ID="2008666770714005"
def num(x):
 try:return float(x or 0)
 except:return 0.0
def is_speaker(title):
 t=(title or "").lower().replace("-"," ")
 keys=("bocina","altavoz","parlante","speaker","jbl go","jblgo","marshall","willen","emberton","sony srs","srs xb")
 return any(k in t for k in keys)
def unit_cost(title):
 t=(title or "").lower().replace("-"," ")
 if "go 5" in t or "go5" in t:return 280.0,"GO5"
 if "go 4" in t or "go4" in t:return 233.0,"GO4"
 if "sony" in t or "srs xb" in t or "srsxb" in t:return 320.0,"SONY"
 if "willen" in t:return 320.0,"WILLEN"
 if "emberton" in t:return 430.0,"EMBERTON"
 return None,"UNKNOWN"
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"]},timeout=TIMEOUT)
r.raise_for_status();tok=r.json()
with open("/tmp/rocio_historical_rotated","w") as f:f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}; me=requests.get(f"{API}/users/me",headers=H,timeout=TIMEOUT).json(); seller=int(me["id"])
start=datetime(2026,1,1,tzinfo=TZ); now=datetime.now(TZ); orders=[];offset=0
while True:
 q=requests.get(f"{API}/orders/search",headers=H,params={"seller":seller,"order.date_created.from":start.isoformat(timespec="milliseconds"),"order.date_created.to":now.isoformat(timespec="milliseconds"),"sort":"date_asc","limit":50,"offset":offset},timeout=TIMEOUT)
 q.raise_for_status();d=q.json();rows=d.get("results") or [];orders.extend(rows);offset+=len(rows)
 if not rows or offset>=int((d.get("paging") or {}).get("total") or 0):break
selected=[]
for o in orders:
 if o.get("status") in {"cancelled","invalid"}:continue
 tags=set(o.get("tags") or []); payments=o.get("payments") or []
 if not (o.get("status") in {"paid","partially_refunded"} or "paid" in tags or any(p.get("status") in {"approved","refunded","charged_back"} for p in payments)):continue
 speaker_items=[i for i in (o.get("order_items") or []) if is_speaker((i.get("item") or {}).get("title"))]
 if speaker_items:selected.append((o,speaker_items))
def external_costs(pair):
 o,speaker_items=pair;oid=o.get("id");all_items=o.get("order_items") or []
 speaker_gross=sum(num(i.get("unit_price"))*int(i.get("quantity") or 0) for i in speaker_items)
 order_gross=sum(num(i.get("unit_price"))*int(i.get("quantity") or 0) for i in all_items)
 share=speaker_gross/order_gross if order_gross else 0
 outbound=0.0;ship_http=None;sid=(o.get("shipping") or {}).get("id")
 if sid:
  x=requests.get(f"{API}/shipments/{sid}/costs",headers=H,timeout=TIMEOUT);ship_http=x.status_code
  if x.status_code==200:
   sd=x.json();senders=sd.get("senders") or [];matched=False
   for z in senders:
    if str(z.get("user_id"))==str(seller):outbound+=num(z.get("cost"));matched=True
   if not matched and len(senders)==1:outbound+=num(senders[0].get("cost"))
 claims=[];return_cost=0.0;claim_http=None
 c=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,params={"resource_id":oid,"limit":50},timeout=TIMEOUT);claim_http=c.status_code
 if c.status_code==200:
  for claim in c.json().get("data") or []:
   cid=claim.get("id")
   if not cid:continue
   rc=requests.get(f"{API}/post-purchase/v1/claims/{cid}/charges/return-cost",headers=H,timeout=TIMEOUT)
   amount=num(rc.json().get("amount")) if rc.status_code==200 else 0.0
   return_cost+=amount;claims.append({"claim_id":cid,"status":claim.get("status"),"return_cost":amount,"return_http":rc.status_code})
 refund=sum(num(p.get("transaction_amount_refunded")) or (num(p.get("transaction_amount")) if p.get("status") in {"refunded","charged_back"} else 0) for p in (o.get("payments") or []))
 return {"order_id":oid,"date":o.get("date_created"),"speaker_gross":speaker_gross,"share":share,"outbound":outbound*share,"refund":refund*share,"return_cost":return_cost*share,"claims":claims,"ship_http":ship_http,"claim_http":claim_http}
external=[]
with ThreadPoolExecutor(max_workers=8) as pool:
 fs=[pool.submit(external_costs,p) for p in selected]
 for f in as_completed(fs):external.append(f.result())
by_order={x["order_id"]:x for x in external}
products={};gross=commissions=cogs=0.0;units=0;unknown={}
first_date=None
for o,items in selected:
 if first_date is None or o.get("date_created","")<first_date:first_date=o.get("date_created")
 for i in items:
  item=i.get("item") or {};title=item.get("title") or "";iid=item.get("id") or "SIN_ID";qty=int(i.get("quantity") or 0);line=num(i.get("unit_price"))*qty;uc,kind=unit_cost(title)
  units+=qty;gross+=line;commissions+=num(i.get("sale_fee"))
  p=products.setdefault(iid,{"item_id":iid,"title":title,"kind":kind,"units":0,"gross":0.0,"unit_cost":uc})
  p["units"]+=qty;p["gross"]+=line
  if uc is None:unknown[iid]={"item_id":iid,"title":title,"units":p["units"]}
  else:cogs+=uc*qty
outbound=sum(x["outbound"] for x in external);refunds=sum(x["refund"] for x in external);return_costs=sum(x["return_cost"] for x in external)
taxes=sum(num((o.get("taxes") or {}).get("amount"))*(by_order[o.get("id")]["share"]) for o,_ in selected)
profit=gross-commissions-outbound-taxes-refunds-return_costs-cogs
result={"seller_id":seller,"nickname":me.get("nickname"),"from":first_date,"to":now.isoformat(),"orders":len(selected),"units":units,"gross":round(gross,2),"commissions":round(commissions,2),"outbound_shipping":round(outbound,2),"taxes":round(taxes,2),"refunds":round(refunds,2),"return_shipping_cost":round(return_costs,2),"cogs_plus_operations":round(cogs,2),"profit":round(profit,2),"partner_50_percent":round(profit/2,2),"unknown_cost_products":list(unknown.values()),"return_claims":[x for x in external if x["claims"]],"api_errors":{"shipment":[x for x in external if x["ship_http"] not in (None,200)],"claims":[x for x in external if x["claim_http"]!=200]},"products":sorted(products.values(),key=lambda p:-p["gross"])}
print("ROCIO_HISTORICAL_PARTNER="+json.dumps(result,ensure_ascii=False),flush=True)
