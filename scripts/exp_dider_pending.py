#!/usr/bin/env python3
# Genera PDF con las etiquetas DIDER en ready_to_print que NO estaban en el batch anterior (44 IDs).
import os, io, json, requests, textwrap
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

API="https://api.mercadolibre.com"
SELLER_ID=3654003391
OUT="ETIQUETAS_DIDER_PENDIENTES.pdf"

# 44 IDs que YA salieron en el PDF anterior
ALREADY={"47917719755","47917737994","47917788540","47917825813","47917945646","47918025078","47918025716","47918054015","47918142733","47918383369","47918398024","47918496206","47918503884","47918570755","47918673831","47918784870","47918803532","47918893308","47918913620","47919009015","47919087567","47919471103","47919573268","47919662959","47919674326","47919690133","47919742150","47919840921","47920050252","47920212092","47920222564","47920325648","47920352816","47920477635","47920540642","47920549347","47920614063","47920711667","47920814301","47920903807","47921112403","47921115056","47921115275","47921152612"}

r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
if r.status_code!=200: raise RuntimeError(f"Token HTTP {r.status_code}: {r.text[:300]}")
tok=r.json()
with open("/tmp/dider_labels_rotated_token","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20); me.raise_for_status()
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

# Clasificar TODOS los shipments actuales
all_r2s={}    # ready_to_ship (cualquier substatus)
r2p_active={} # ready_to_print (o printed) - accionables
for sid,rows in by_sid.items():
 q=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=20)
 if q.status_code!=200: continue
 sh=q.json()
 st=sh.get("status"); sub=sh.get("substatus")
 if st!="ready_to_ship": continue
 all_r2s[sid]={"substatus":sub,"rows":rows}
 if sub in {"ready_to_print","printed"}:
  r2p_active[sid]={"substatus":sub,"rows":rows}

pending_ids=sorted(set(r2p_active.keys()) - ALREADY, key=lambda x:int(x))
print(f"[stats] total ready_to_ship: {len(all_r2s)}")
print(f"[stats] ready_to_print/printed: {len(r2p_active)}")
print(f"[stats] ya en PDF previo (ALREADY): {len(ALREADY)}")
print(f"[stats] pendientes NUEVOS: {len(pending_ids)} -> {pending_ids}")

# Reportar substatus breakdown
from collections import Counter
bd=Counter(v["substatus"] for v in all_r2s.values())
print(f"[breakdown] {dict(bd)}")

# Diff inverso: ¿alguno del ALREADY ya NO está en r2p_active?
gone=sorted(ALREADY - set(r2p_active.keys()), key=lambda x:int(x))
print(f"[info] del batch previo (44) YA no accionables: {len(gone)} -> {gone[:10]}")

if not pending_ids:
 print("Sin pendientes nuevos. Saliendo.")
 with open("MANIFEST_DIDER_PENDIENTES.json","w") as f:
  json.dump({"pending":[],"all_r2s":len(all_r2s),"r2p_active":len(r2p_active),"gone_from_batch":gone,"breakdown":dict(bd)},f,indent=2,ensure_ascii=False)
 open(OUT,"wb").close()
 raise SystemExit(0)

selected=[]
for sid in pending_ids:
 rows=r2p_active[sid]["rows"]
 products=OrderedDict()
 for order in rows:
  for line in order.get("order_items") or []:
   obj=line.get("item") or {}
   title=(obj.get("title") or "Producto sin título").strip()
   qty=int(line.get("quantity") or 0)
   products[title]=products.get(title,0)+qty
 contents=[{"quantity":qty,"title":title} for title,qty in products.items()]
 selected.append({"shipment_id":sid,"substatus":r2p_active[sid]["substatus"],"order_ids":[str(x.get("id")) for x in rows],"contents":contents})

def header_overlay(width,height,header_h,shipment_id,contents):
 buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(width,height))
 c.setFillColor(Color(1,0.95,0.55)); c.rect(0,height-header_h,width,header_h,fill=1,stroke=0)
 c.setStrokeColorRGB(0,0,0); c.line(0,height-header_h,width,height-header_h)
 c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold",8)
 c.drawCentredString(width/2,height-11,f"DIDER - ENVIO {shipment_id}")
 lines=[]
 for x in contents:
  prefix=f"{x['quantity']} x "
  wrapped=textwrap.wrap(prefix+x["title"],width=48,break_long_words=False,break_on_hyphens=False) or [prefix+x["title"]]
  lines.extend(wrapped)
 fs=8 if len(lines)<=5 else 7
 leading=9 if fs==8 else 8
 c.setFont("Helvetica-Bold",fs)
 y=height-23
 for line in lines:
  c.drawCentredString(width/2,y,line[:65]); y-=leading
 c.showPage(); c.save(); buf.seek(0)
 return PdfReader(buf).pages[0]

writer=PdfWriter(); manifest=[]; failed=[]
for x in selected:
 sid=x["shipment_id"]
 q=requests.get(f"{API}/shipment_labels",headers=H,params={
  "shipment_ids":sid,"response_type":"pdf","savePdf":"Y"},timeout=40)
 if q.status_code!=200 or "application/pdf" not in q.headers.get("content-type","").lower():
  failed.append({"shipment_id":sid,"http":q.status_code,"detail":q.text[:200]}); continue
 reader=PdfReader(io.BytesIO(q.content))
 for p in reader.pages:
  W=float(p.mediabox.width); Hh=float(p.mediabox.height)
  header_h=max(30, int(Hh*0.07))
  overlay=header_overlay(W,Hh,header_h,sid,x["contents"])
  merged=PageObject.create_blank_page(width=W,height=Hh)
  merged.merge_page(p)
  merged.merge_page(overlay)
  writer.add_page(merged)
 manifest.append({"shipment_id":sid,"substatus":x["substatus"],"order_ids":x["order_ids"],"contents":x["contents"]})

with open(OUT,"wb") as f: writer.write(f)
with open("MANIFEST_DIDER_PENDIENTES.json","w") as f:
 json.dump({"seller_id":SELLER_ID,"generated_at":now.isoformat(),"unique_shipments":len(manifest),"pages":len(writer.pages),"shipments":manifest,"failed":failed,"stats":{"all_r2s":len(all_r2s),"r2p_active":len(r2p_active),"already_in_prev_pdf":len(ALREADY),"gone_from_batch":gone,"breakdown":dict(bd)}},f,indent=2,ensure_ascii=False)
print(f"OK {OUT} pages={len(writer.pages)} shipments={len(manifest)} failed={len(failed)}")
