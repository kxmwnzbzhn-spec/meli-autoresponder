#!/usr/bin/env python3
"""DIDER: one visible unit, unlimited restock, and bounded catalog pricing."""
import json, os, time, requests

API="https://api.mercadolibre.com"; SELLER_ID=3654003391
TIMEOUT=30; TICK=30; DURATION=int(os.environ.get("RUN_DURATION_SEC","19800"))
with open("config/dider_autostock_unlimited.json") as f:
    ITEM_IDS=list(dict.fromkeys(json.load(f)))
try:
    with open("config/dider_price_bounds.json") as f: PRICE_BOUNDS=json.load(f)
except FileNotFoundError:
    PRICE_BOUNDS={}

r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"]},timeout=TIMEOUT)
r.raise_for_status(); tok=r.json()
open("/tmp/dider_rotated_token","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=TIMEOUT); me.raise_for_status()
if int(me.json().get("id") or 0)!=SELLER_ID: raise RuntimeError("Token no corresponde a DIDER")

def item(iid):
 q=requests.get(f"{API}/items/{iid}",headers=H,timeout=TIMEOUT); q.raise_for_status(); d=q.json()
 if int(d.get("seller_id") or 0)!=SELLER_ID: raise RuntimeError(f"{iid}: seller inesperado")
 return d

def stock(iid,initial=False):
 d=item(iid); status=d.get("status"); qty=int(d.get("available_quantity") or 0)
 if initial: print(f"[STOCK] {iid} unlimited status={status} qty={qty}",flush=True)
 if status=="active" and qty==1: return
 if status not in {"active","paused"}:
  print(f"[POLICY-SKIP] {iid} status={status} sub={d.get('sub_status')}",flush=True); return
 body={"available_quantity":1}
 if status=="paused": body["status"]="active"
 u=requests.put(f"{API}/items/{iid}",headers=HJ,json=body,timeout=TIMEOUT)
 if u.status_code not in (200,201): raise RuntimeError(f"{iid}: stock HTTP {u.status_code} {u.text[:500]}")
 z=item(iid)
 if z.get("status")!="active" or int(z.get("available_quantity") or 0)!=1:
  raise RuntimeError(f"{iid}: stock verify status={z.get('status')} qty={z.get('available_quantity')}")
 print(f"[REPLENISHED] {iid} unlimited qty=1",flush=True)

def price(iid):
 b=PRICE_BOUNDS.get(iid)
 if not b: return
 d=item(iid); floor=float(b["floor"]); ceiling=float(b["ceiling"]); current=float(d.get("price") or 0)
 if d.get("status")!="active": return
 cpid=d.get("catalog_product_id"); external=[]
 if cpid:
  q=requests.get(f"{API}/products/{cpid}/items",headers=H,params={"limit":50},timeout=TIMEOUT)
  if q.status_code==200:
   own_linked=set(ITEM_IDS)|{str(v.get("source_item")) for v in PRICE_BOUNDS.values() if v.get("source_item")}
   for x in q.json().get("results") or []:
    if x.get("item_id") not in own_linked and x.get("status","active")=="active" and x.get("price") is not None:
     external.append(float(x["price"]))
 step=float(b.get("step") or 10)
 raw=(min(external)-step if external else ceiling)
 if b.get("force_price_to_win"):
  w=requests.get(f"{API}/items/{iid}/price_to_win",headers=H,params={"version":"v2"},timeout=TIMEOUT)
  if w.status_code==200:
   wd=w.json(); ptw=wd.get("price_to_win")
   if ptw is not None:
    raw=float(ptw)-step
    print(f"[PRICE-TO-WIN] {iid} status={wd.get('status')} ptw={ptw} target_raw={raw}",flush=True)
 target=min(ceiling,max(floor,raw))
 target=round(target,2)
 if abs(current-target)<1: return
 u=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=TIMEOUT)
 if u.status_code not in (200,201): raise RuntimeError(f"{iid}: price HTTP {u.status_code} {u.text[:500]}")
 z=item(iid)
 if not floor<=float(z.get("price") or 0)<=ceiling: raise RuntimeError(f"{iid}: price fuera de rango")
 print(f"[PRICE] {iid} {current}->{z.get('price')} bounds={floor}-{ceiling}",flush=True)

for iid in ITEM_IDS: stock(iid,True)
for iid in PRICE_BOUNDS: price(iid)
started=time.time(); cycles=0
while time.time()-started<DURATION:
 cycles+=1; cycle=time.time()
 for iid in ITEM_IDS:
  try: stock(iid)
  except Exception as exc: print(f"[ERROR-STOCK] {iid}: {exc}",flush=True)
 if cycles%10==0:
  for iid in PRICE_BOUNDS:
   try: price(iid)
   except Exception as exc: print(f"[ERROR-PRICE] {iid}: {exc}",flush=True)
 time.sleep(max(0,TICK-(time.time()-cycle)))
print(f"[END] cycles={cycles} items={len(ITEM_IDS)} priced={len(PRICE_BOUNDS)}",flush=True)
