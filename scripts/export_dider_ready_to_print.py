#!/usr/bin/env python3
import os, io, json, requests
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter

API="https://api.mercadolibre.com"
SELLER_ID=3654003391
OUT="ETIQUETAS_DIDER_LISTAS_PARA_IMPRIMIR.pdf"

r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
if r.status_code!=200:
 raise RuntimeError(f"Token HTTP {r.status_code}: {r.text[:300]}")
tok=r.json()
with open("/tmp/dider_labels_rotated_token","w") as f:f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20);me.raise_for_status()
if int(me.json().get("id") or 0)!=SELLER_ID: raise RuntimeError("Cuenta DIDER incorrecta")

now=datetime.now(timezone.utc); start=now-timedelta(days=60)
orders=[]; off=0
while True:
 q=requests.get(f"{API}/orders/search",headers=H,params={
  "seller":SELLER_ID,"order.status":"paid",
  "order.date_created.from":start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
  "order.date_created.to":now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
  "limit":50,"offset":off,"sort":"date_desc"},timeout=30)
 q.raise_for_status(); body=q.json(); rows=body.get("results") or []
 orders.extend(rows); off+=len(rows)
 if not rows or off>=int((body.get("paging") or {}).get("total") or 0): break

by_sid={}
for order in orders:
 sid=(order.get("shipping") or {}).get("id")
 if sid: by_sid.setdefault(str(sid),[]).append(order)

selected=[]
for sid,rows in by_sid.items():
 q=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=20)
 if q.status_code!=200: continue
 sh=q.json()
 if sh.get("status")=="ready_to_ship" and sh.get("substatus")=="ready_to_print":
  selected.append({"shipment_id":sid,"order_ids":[str(x.get("id")) for x in rows]})
selected.sort(key=lambda x:int(x["shipment_id"]))

writer=PdfWriter(); manifest=[]; failed=[]
for x in selected:
 sid=x["shipment_id"]
 q=requests.get(f"{API}/shipment_labels",headers=H,params={
  "shipment_ids":sid,"response_type":"pdf","savePdf":"Y"},timeout=40)
 if q.status_code!=200 or "application/pdf" not in q.headers.get("content-type","").lower():
  failed.append({"shipment_id":sid,"http":q.status_code,"detail":q.text[:200]});continue
 reader=PdfReader(io.BytesIO(q.content))
 if not reader.pages:
  failed.append({"shipment_id":sid,"detail":"PDF sin páginas"});continue
 writer.add_page(reader.pages[0])
 manifest.append(x)

with open(OUT,"wb") as f: writer.write(f)
with open("MANIFEST_DIDER.json","w") as f: json.dump({
 "seller_id":SELLER_ID,"status":"ready_to_ship","substatus":"ready_to_print",
 "unique_shipments":len(manifest),"pages":len(writer.pages),"shipments":manifest,"failed":failed
},f,ensure_ascii=False,indent=2)
print("DIDER_LABEL_RESULT="+json.dumps({"selected":len(selected),"pages":len(writer.pages),"failed":failed},ensure_ascii=False))
if failed: raise SystemExit("Hubo etiquetas fallidas")
if len(writer.pages)!=len({x["shipment_id"] for x in manifest}): raise SystemExit("Conteo o duplicados incorrectos")
