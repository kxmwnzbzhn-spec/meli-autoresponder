#!/usr/bin/env python3
import os, io, json, requests
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
API="https://api.mercadolibre.com"; SELLER=3658310023
TARGET=set(json.load(open("config/rosa_target_ids.json")))
OUT="ETIQUETAS_ROSA_MARIA_NUEVAS.pdf"
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
  ITEM_CACHE[iid]={"model":"","color":"","condition":"new"}; return ITEM_CACHE[iid]
 it=g.json()
 attrs={(a.get("id") or "").upper():(a.get("value_name") or "") for a in (it.get("attributes") or [])}
 model=attrs.get("MODEL") or ""; color=attrs.get("COLOR") or attrs.get("MAIN_COLOR") or ""
 cond=it.get("condition") or "new"; cpid=it.get("catalog_product_id")
 if (not model or model.lower() in ("general","otro","genérico","generico")) and cpid:
  pj=PROD_CACHE.get(cpid)
  if pj is None:
   pg=requests.get(f"{API}/products/{cpid}",headers=H,timeout=20)
   pj=pg.json() if pg.status_code==200 else {}; PROD_CACHE[cpid]=pj
  pattrs={(a.get("id") or "").upper():(a.get("value_name") or "") for a in (pj.get("attributes") or [])}
  if pattrs.get("MODEL") and pattrs["MODEL"].lower() not in ("general","otro"): model=pattrs["MODEL"]
  if not color: color=pattrs.get("COLOR") or pattrs.get("MAIN_COLOR") or ""
 ITEM_CACHE[iid]={"model":model.strip(),"color":color.strip(),"condition":cond}
 return ITEM_CACHE[iid]

def gc(line, fb):
 for a in (line.get("variation_attributes") or []):
  if (a.get("id") or "").upper()=="COLOR" or "color" in (a.get("name") or "").lower():
   v=(a.get("value_name") or "").strip()
   if v: return v
 return fb

# construir items por shipment desde /shipments/{id} → order_id → /orders/{id}
selected=[]
for sid in sorted(TARGET,key=int):
 sh_r=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=20)
 if sh_r.status_code!=200: continue
 sh=sh_r.json()
 # sacar order_ids del shipment
 order_ids=[str(o.get("id")) for o in (sh.get("order_id") and [{"id":sh["order_id"]}] or [])]
 # /shipments/{id}/items → mejor
 sit=requests.get(f"{API}/shipments/{sid}/items",headers=H,timeout=20)
 items_raw=[]
 if sit.status_code==200:
  for it in (sit.json() if isinstance(sit.json(),list) else []):
   iid=it.get("id"); qty=int(it.get("quantity") or 0)
   at=get_attrs(iid) if iid else {"model":"","color":"","condition":"new"}
   items_raw.append({"qty":qty,"modelo":at["model"],"color":at["color"],"used":at["condition"]=="used","item_id":iid})
 merged=OrderedDict()
 for x in items_raw:
  k=(x["modelo"],x["color"],x["used"])
  if k in merged: merged[k]["qty"]+=x["qty"]
  else: merged[k]=dict(x)
 selected.append({"shipment_id":sid,"substatus":sh.get("substatus"),"items":list(merged.values()),"used":any(x["used"] for x in merged.values()),"multi":sum(x["qty"] for x in merged.values())>=2 and len(merged)>=2})

print(f"[stats] shipments a incluir: {len(selected)}")

def overlay(W,Hh,ship,items,used,multi,sub):
 buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(W,Hh)); y=Hh
 if used:
  bh=14; c.setFillColor(Color(0.85,0.1,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,"*** PRODUCTO USADO ***"); y-=bh
 if multi:
  bh=14; c.setFillColor(Color(1,0.55,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,f">>> ENVIO CON {sum(x['qty'] for x in items)} PRODUCTOS <<<"); y-=bh
 n=len(items); hh=max(30,30+11*max(0,n-1))
 c.setFillColor(Color(1,0.95,0.55)); c.rect(0,y-hh,W,hh,fill=1,stroke=0)
 c.setStrokeColorRGB(0,0,0); c.line(0,y-hh,W,y-hh); c.setFillColorRGB(0,0,0)
 c.setFont("Helvetica",7); c.drawCentredString(W/2,y-9,f"[ROSA-MARIA/{sub}] Ship:{ship}")
 fs=10 if n<=3 else 9; c.setFont("Helvetica-Bold",fs); yy=y-9-11
 for it in items:
  parts=[str(it["qty"])]
  if it["modelo"]: parts.append(it["modelo"])
  if it["color"]: parts.append(it["color"])
  txt=" ".join(parts)
  if it["used"]: txt="USADO "+txt
  c.drawCentredString(W/2,yy,txt[:60]); yy-=11
 c.showPage(); c.save(); buf.seek(0); return PdfReader(buf).pages[0]

writer=PdfWriter(); mfst=[]; failed=[]
for x in selected:
 sid=x["shipment_id"]
 q=requests.get(f"{API}/shipment_labels",headers=H,params={"shipment_ids":sid,"response_type":"pdf","savePdf":"Y"},timeout=40)
 if q.status_code!=200 or "application/pdf" not in q.headers.get("content-type","").lower():
  failed.append({"shipment_id":sid,"http":q.status_code}); continue
 rdr=PdfReader(io.BytesIO(q.content))
 for p in rdr.pages:
  W=float(p.mediabox.width); Hh=float(p.mediabox.height)
  ov=overlay(W,Hh,sid,x["items"],x["used"],x["multi"],x["substatus"] or "")
  m=PageObject.create_blank_page(width=W,height=Hh); m.merge_page(p); m.merge_page(ov); writer.add_page(m)
 mfst.append(x)
with open(OUT,"wb") as f: writer.write(f)
open("MANIFEST_ROSA_MARIA_NUEVAS.json","w").write(json.dumps({"unique":len(mfst),"pages":len(writer.pages),"failed":failed,"shipments":mfst},indent=2,ensure_ascii=False))
print(f"OK {OUT} pages={len(writer.pages)} ship={len(mfst)} failed={len(failed)}")
