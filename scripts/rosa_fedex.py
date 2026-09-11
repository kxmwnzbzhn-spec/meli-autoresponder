#!/usr/bin/env python3
"""Filtrar por carrier FedEx y bajar solo esos labels (1 pág por shipment)."""
import os, io, json, requests
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

API="https://api.mercadolibre.com"; SELLER=3658310023
OUT="ETIQUETAS_ROSA_MARIA_FEDEX.pdf"; MANI="MANIFEST_ROSA_MARIA_FEDEX.json"
IDS=json.load(open("config/rosa_153_ids.json"))

rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=30)
r.raise_for_status(); tok=r.json()
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}

ITEM_CACHE={}; PROD_CACHE={}
def get_attrs(iid):
 if iid in ITEM_CACHE: return ITEM_CACHE[iid]
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=20)
 if g.status_code!=200:
  ITEM_CACHE[iid]={"model":"","color":""}; return ITEM_CACHE[iid]
 it=g.json(); attrs={(a.get("id") or "").upper():(a.get("value_name") or "") for a in (it.get("attributes") or [])}
 model=attrs.get("MODEL") or ""; color=attrs.get("COLOR") or attrs.get("MAIN_COLOR") or ""
 cpid=it.get("catalog_product_id")
 if (not model or model.lower() in ("general","otro")) and cpid:
  pj=PROD_CACHE.get(cpid)
  if pj is None:
   pg=requests.get(f"{API}/products/{cpid}",headers=H,timeout=20)
   pj=pg.json() if pg.status_code==200 else {}; PROD_CACHE[cpid]=pj
  pattrs={(a.get("id") or "").upper():(a.get("value_name") or "") for a in (pj.get("attributes") or [])}
  if pattrs.get("MODEL") and pattrs["MODEL"].lower() not in ("general","otro"): model=pattrs["MODEL"]
  if not color: color=pattrs.get("COLOR") or pattrs.get("MAIN_COLOR") or ""
 ITEM_CACHE[iid]={"model":model.strip(),"color":color.strip()}
 return ITEM_CACHE[iid]

def gc(line, fb):
 for a in (line.get("variation_attributes") or []):
  if (a.get("id") or "").upper()=="COLOR":
   v=(a.get("value_name") or "").strip()
   if v: return v
 return fb

# clasificar por carrier via /shipments/{id}/carrier
selected=[]; carriers_stats={}
from collections import Counter
cnt=Counter()
for sid in IDS:
 c=requests.get(f"{API}/shipments/{sid}/carrier",headers=H,timeout=15)
 carrier_name = (c.json().get("name") if c.status_code==200 else "") or ""
 cnt[carrier_name]+=1
 if "fedex" not in carrier_name.lower(): continue
 # bajar order items
 oq=requests.get(f"{API}/orders/search",headers=H,params={"seller":SELLER,"shipping.id":sid,"limit":50},timeout=30)
 orders=(oq.json().get("results") or []) if oq.status_code==200 else []
 items=[]
 for order in orders:
  for line in (order.get("order_items") or []):
   obj=line.get("item") or {}
   iid=obj.get("id"); qty=int(line.get("quantity") or 0)
   if not iid: continue
   at=get_attrs(iid); color=gc(line, at["color"])
   items.append({"qty":qty,"modelo":at["model"],"color":color})
 selected.append({"shipment_id":sid,"carrier":carrier_name,"service":svc_name,"items":items})

print(f"[stats] carriers breakdown: {dict(cnt)}"); carriers_stats=dict(cnt)
print(f"[stats] FedEx seleccionadas: {len(selected)}")

def overlay(W,Hh,ship,items):
 buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(W,Hh)); y=Hh
 hh=max(30,30+11*max(0,len(items)-1))
 c.setFillColor(Color(1,0.95,0.55)); c.rect(0,y-hh,W,hh,fill=1,stroke=0)
 c.setStrokeColorRGB(0,0,0); c.line(0,y-hh,W,y-hh); c.setFillColorRGB(0,0,0)
 c.setFont("Helvetica",7); c.drawCentredString(W/2,y-9,f"[ROSA-MARIA/FEDEX] Ship:{ship}")
 fs=10 if len(items)<=3 else 9; c.setFont("Helvetica-Bold",fs); yy=y-9-11
 for it in items:
  parts=[str(it["qty"])]
  if it["modelo"]: parts.append(it["modelo"])
  if it["color"]: parts.append(it["color"])
  c.drawCentredString(W/2,yy," ".join(parts)[:60]); yy-=11
 c.showPage(); c.save(); buf.seek(0); return PdfReader(buf).pages[0]

writer=PdfWriter(); manifest=[]; failed=[]
for x in selected:
 sid=x["shipment_id"]
 q=requests.get(f"{API}/shipment_labels",headers=H,params={"shipment_ids":sid,"response_type":"pdf","savePdf":"Y"},timeout=40)
 if q.status_code!=200 or "application/pdf" not in q.headers.get("content-type","").lower():
  failed.append({"shipment_id":sid,"http":q.status_code}); continue
 rdr=PdfReader(io.BytesIO(q.content))
 pages=list(rdr.pages)
 if pages:
  p=pages[0]
  W=float(p.mediabox.width); Hh=float(p.mediabox.height)
  ov=overlay(W,Hh,sid,x["items"])
  m=PageObject.create_blank_page(width=W,height=Hh); m.merge_page(p); m.merge_page(ov); writer.add_page(m)
 manifest.append(x)
with open(OUT,"wb") as f: writer.write(f)
open(MANI,"w").write(json.dumps({"total":len(manifest),"pages":len(writer.pages),"failed":failed,"carriers_stats":carriers_stats,"shipments":manifest},indent=2,ensure_ascii=False))
print(f"OK {OUT} pages={len(writer.pages)} ship={len(manifest)} failed={len(failed)}")
