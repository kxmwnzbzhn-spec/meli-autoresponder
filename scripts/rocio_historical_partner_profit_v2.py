#!/usr/bin/env python3
"""Auditoría histórica v2 de utilidad de bocinas ROCIOANGEL, con reclamos y costo de retorno."""
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

API="https://api.mercadolibre.com"; TZ=ZoneInfo("America/Mexico_City"); TIMEOUT=30
def n(x):
 try:return float(x or 0)
 except:return 0.0
def speaker(title):
 t=(title or "").lower().replace("-"," ")
 return any(k in t for k in ("bocina","altavoz","parlante","speaker","jbl go","jblgo","marshall","willen","emberton","sony srs","srs xb"))
def cost(title):
 t=(title or "").lower().replace("-"," ")
 if "go 5" in t or "go5" in t:return 280.0,"GO5"
 if "go 4" in t or "go4" in t:return 233.0,"GO4"
 if "sony" in t or "srs xb" in t or "srsxb" in t:return 320.0,"SONY"
 if "willen" in t:return 320.0,"WILLEN"
 if "emberton" in t:return 430.0,"EMBERTON"
 return None,"UNKNOWN"
auth=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":"2008666770714005","client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"]},timeout=TIMEOUT)
auth.raise_for_status();td=auth.json()
with open("/tmp/rocio_historical_v2_rotated","w") as f:f.write(td.get("refresh_token",""))
H={"Authorization":f"Bearer {td['access_token']}"};me=requests.get(f"{API}/users/me",headers=H,timeout=TIMEOUT).json();seller=int(me["id"])
start=datetime(2026,1,1,tzinfo=TZ);now=datetime.now(TZ)
orders=[];offset=0
while True:
 r=requests.get(f"{API}/orders/search",headers=H,params={"seller":seller,"order.date_created.from":start.isoformat(timespec="milliseconds"),"order.date_created.to":now.isoformat(timespec="milliseconds"),"sort":"date_asc","limit":50,"offset":offset},timeout=TIMEOUT)
 r.raise_for_status();d=r.json();batch=d.get("results") or [];orders+=batch;offset+=len(batch)
 if not batch or offset>=int((d.get("paging") or {}).get("total") or 0):break
selected={}
for o in orders:
 if o.get("status") in {"cancelled","invalid"}:continue
 tags=set(o.get("tags") or []);pays=o.get("payments") or []
 if not (o.get("status") in {"paid","partially_refunded"} or "paid" in tags or any(p.get("status") in {"approved","refunded","charged_back"} for p in pays)):continue
 si=[i for i in (o.get("order_items") or []) if speaker((i.get("item") or {}).get("title"))]
 if si:selected[int(o["id"])]=(o,si)

def outbound(pair):
 oid,(o,si)=pair;all_items=o.get("order_items") or []
 sg=sum(n(i.get("unit_price"))*int(i.get("quantity") or 0) for i in si);og=sum(n(i.get("unit_price"))*int(i.get("quantity") or 0) for i in all_items);share=sg/og if og else 0
 sid=(o.get("shipping") or {}).get("id");amount=0.0;http=None
 if sid:
  r=requests.get(f"{API}/shipments/{sid}/costs",headers=H,timeout=TIMEOUT);http=r.status_code
  if http==200:
   senders=r.json().get("senders") or [];matched=False
   for x in senders:
    if str(x.get("user_id"))==str(seller):amount+=n(x.get("cost"));matched=True
   if not matched and len(senders)==1:amount+=n(senders[0].get("cost"))
 refund=sum(n(p.get("transaction_amount_refunded")) or (n(p.get("transaction_amount")) if p.get("status") in {"refunded","charged_back"} else 0) for p in (o.get("payments") or []))
 return oid,{"share":share,"outbound":amount*share,"refund":refund*share,"ship_http":http}
ext={}
with ThreadPoolExecutor(max_workers=8) as pool:
 fs=[pool.submit(outbound,p) for p in selected.items()]
 for f in as_completed(fs):
  oid,data=f.result();ext[oid]=data

# Consulta de reclamos acotada correctamente por vendedor y rango.
claims=[];offset=0
range_value=f"date_created:after:{start.isoformat(timespec='milliseconds')},before:{now.isoformat(timespec='milliseconds')}"
while True:
 r=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,params={"players.user_id":seller,"players.role":"respondent","range":range_value,"limit":50,"offset":offset},timeout=TIMEOUT)
 if r.status_code==429:
  import time;time.sleep(2);continue
 r.raise_for_status();d=r.json();batch=d.get("data") or [];claims+=batch;offset+=len(batch)
 if not batch or offset>=int((d.get("paging") or {}).get("total") or 0):break
relevant=[c for c in claims if c.get("resource")=="order" and int(c.get("resource_id") or 0) in selected]
def return_charge(c):
 cid=c["id"];r=requests.get(f"{API}/post-purchase/v1/claims/{cid}/charges/return-cost",headers=H,timeout=TIMEOUT)
 return {"claim_id":cid,"order_id":int(c.get("resource_id")),"type":c.get("type"),"status":c.get("status"),"reason_id":c.get("reason_id"),"amount":n(r.json().get("amount")) if r.status_code==200 else 0.0,"http":r.status_code}
charges=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 fs=[pool.submit(return_charge,c) for c in relevant]
 for f in as_completed(fs):charges.append(f.result())
return_by_order={}
for c in charges:return_by_order[c["order_id"]]=return_by_order.get(c["order_id"],0.0)+c["amount"]

gross=fees=cogs=taxes=0.0;units=0;unknown=[];products={};first=None
for oid,(o,items) in selected.items():
 dt=o.get("date_created")
 if first is None or dt<first:first=dt
 for i in items:
  item=i.get("item") or {};title=item.get("title") or "";iid=item.get("id") or "SIN_ID";qty=int(i.get("quantity") or 0);line=n(i.get("unit_price"))*qty;uc,kind=cost(title)
  units+=qty;gross+=line;fees+=n(i.get("sale_fee"))
  p=products.setdefault(iid,{"item_id":iid,"title":title,"kind":kind,"units":0,"gross":0.0,"unit_cost":uc});p["units"]+=qty;p["gross"]+=line
  if uc is None:unknown.append({"item_id":iid,"title":title,"units":qty})
  else:cogs+=uc*qty
 taxes+=n((o.get("taxes") or {}).get("amount"))*ext[oid]["share"]
outbound_total=sum(x["outbound"] for x in ext.values());refunds=sum(x["refund"] for x in ext.values())
return_total=sum(return_by_order.get(oid,0.0)*ext[oid]["share"] for oid in selected)
profit=gross-fees-outbound_total-taxes-refunds-return_total-cogs
out={"seller_id":seller,"from":first,"to":now.isoformat(),"orders":len(selected),"units":units,"gross":round(gross,2),"commissions":round(fees,2),"outbound_shipping":round(outbound_total,2),"taxes":round(taxes,2),"refunds":round(refunds,2),"return_shipping_cost":round(return_total,2),"cogs_plus_operations":round(cogs,2),"profit":round(profit,2),"partner_50_percent":round(profit/2,2),"claims_found":len(relevant),"return_cost_records":charges,"unknown_cost_products":unknown,"shipment_errors":[{"order_id":oid,"http":x["ship_http"]} for oid,x in ext.items() if x["ship_http"] not in (None,200)],"products":sorted(products.values(),key=lambda p:-p["gross"])}
print("ROCIO_HISTORICAL_PARTNER_V2="+json.dumps(out,ensure_ascii=False),flush=True)
