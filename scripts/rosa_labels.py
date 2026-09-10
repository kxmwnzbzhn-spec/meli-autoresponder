#!/usr/bin/env python3
"""ROSA_MARIA: consolidar ready_to_print + demoradas. Modelo/color EXACTO desde item.attributes."""
import os, io, json, requests
from collections import OrderedDict, Counter
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

API="https://api.mercadolibre.com"; SELLER=3658310023
OUT="ETIQUETAS_ROSA_MARIA.pdf"; MANI="MANIFEST_ROSA_MARIA.json"

rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=30)
r.raise_for_status(); tok=r.json()
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print(f"[auth] uid={me.get('id')} nick={me.get('nickname')}")
if int(me.get("id") or 0)!=SELLER: raise SystemExit(f"seller mismatch: {me.get('id')}")

ITEM_CACHE={}; PROD_CACHE={}
def get_attrs(iid):
 if iid in ITEM_CACHE: return ITEM_CACHE[iid]
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=20)
 if g.status_code!=200:
  ITEM_CACHE[iid]={"model":"","color":"","condition":"new","cpid":None}; return ITEM_CACHE[iid]
 it=g.json()
 attrs={(a.get("id") or "").upper():(a.get("value_name") or "") for a in (it.get("attributes") or [])}
 model=attrs.get("MODEL") or ""
 color=attrs.get("COLOR") or attrs.get("MAIN_COLOR") or ""
 cond=it.get("condition") or "new"
 cpid=it.get("catalog_product_id")
 # si model vacío o "General", intentar catálogo
 if (not model or model.lower() in ("general","otro","genérico","generico")) and cpid:
  if cpid in PROD_CACHE: pj=PROD_CACHE[cpid]
  else:
   pg=requests.get(f"{API}/products/{cpid}",headers=H,timeout=20)
   pj=pg.json() if pg.status_code==200 else {}
   PROD_CACHE[cpid]=pj
  pattrs={(a.get("id") or "").upper():(a.get("value_name") or "") for a in (pj.get("attributes") or [])}
  if pattrs.get("MODEL") and pattrs["MODEL"].lower() not in ("general","otro"):
   model=pattrs["MODEL"]
  if not color: color=pattrs.get("COLOR") or pattrs.get("MAIN_COLOR") or ""
 ITEM_CACHE[iid]={"model":model.strip(),"color":color.strip(),"condition":cond,"cpid":cpid}
 return ITEM_CACHE[iid]

def get_color_variation(line, fallback_color):
 # Preferir variation_attributes de la orden (por si es variante)
 for a in (line.get("variation_attributes") or []):
  if (a.get("id") or "").upper()=="COLOR" or "color" in (a.get("name") or "").lower():
   v=(a.get("value_name") or "").strip()
   if v: return v
 item=line.get("item") or {}
 iid=item.get("id"); vid=item.get("variation_id")
 if iid and vid:
  try:
   g=requests.get(f"{API}/items/{iid}/variations/{vid}",headers=H,timeout=15)
   if g.status_code==200:
    for a in (g.json().get("attribute_combinations") or []):
     if (a.get("id") or "").upper()=="COLOR":
      v=(a.get("value_name") or "").strip()
      if v: return v
  except Exception: pass
 return fallback_color

now=datetime.now(timezone.utc); start=now-timedelta(days=90)
today_date=now.date()
orders=[]; off=0
while True:
 q=requests.get(f"{API}/orders/search",headers=H,params={
  "seller":SELLER,"order.status":"paid",
  "order.date_created.from":start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
  "order.date_created.to":now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
  "limit":50,"offset":off,"sort":"date_desc"},timeout=30)
 q.raise_for_status(); body=q.json(); rows=body.get("results") or []
 orders.extend(rows); off+=len(rows)
 if not rows or off>=int((body.get("paging") or {}).get("total") or 0): break
by_sid={}
for o in orders:
 sid=(o.get("shipping") or {}).get("id")
 if sid: by_sid.setdefault(str(sid),[]).append(o)

sub_stats=Counter(); selected=[]; delayed_count=0; r2p_count=0
for sid,rows in by_sid.items():
 q=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=20)
 if q.status_code!=200: continue
 sh=q.json()
 if sh.get("status")!="ready_to_ship": continue
 sub=sh.get("substatus"); sub_stats[sub]+=1
 # Determinar si demorada
 dh=sh.get("date_handling") or {}
 lim=dh.get("estimated_handling_limit") or {}
 lim_date=lim.get("date")
 is_delayed=False
 if lim_date:
  try:
   ldt=datetime.fromisoformat(lim_date.replace("Z","+00:00"))
   if ldt < now: is_delayed=True
  except Exception: pass
 is_r2p = sub in ('ready_to_print','printed')
 if not (is_r2p or is_delayed): continue
 tag=[]
 if is_delayed: tag.append("DEMORADA"); delayed_count+=1
 if is_r2p: tag.append("READY"); r2p_count+=1
 items=[]; any_used=False
 for order in rows:
  for line in order.get("order_items") or []:
   obj=line.get("item") or {}
   qty=int(line.get("quantity") or 0)
   iid=obj.get("id") or ""
   if not iid: continue
   at=get_attrs(iid)
   color = get_color_variation(line, at["color"])
   if at["condition"]=="used": any_used=True
   items.append({"qty":qty,"modelo":at["model"],"color":color,"used":at["condition"]=="used","item_id":iid})
 merged=OrderedDict()
 for x in items:
  k=(x["modelo"],x["color"],x["used"])
  if k in merged: merged[k]["qty"]+=x["qty"]
  else: merged[k]=dict(x)
 selected.append({"shipment_id":sid,"tag":"+".join(tag),"substatus":sub,"delayed":is_delayed,"lim_date":lim_date,"items":list(merged.values()),"used":any_used,"multi":sum(x["qty"] for x in merged.values())>=2 and len(merged)>=2,"order_ids":[str(o.get("id")) for o in rows]})

# Ordenar: demoradas primero, luego ready_to_print, por shipment
selected.sort(key=lambda x:(0 if x["delayed"] else 1, int(x["shipment_id"])))
print(f"[stats] breakdown={dict(sub_stats)}")
print(f"[stats] demoradas={delayed_count} ready_to_print={r2p_count} total_seleccionados={len(selected)}")

def overlay(W,Hh,ship,tag,items,used,multi,delayed):
 buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(W,Hh))
 y=Hh
 if used:
  bh=14; c.setFillColor(Color(0.85,0.1,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,"*** PRODUCTO USADO ***"); y-=bh
 if delayed:
  bh=14; c.setFillColor(Color(0.85,0.1,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,f"!!! DEMORADA !!!"); y-=bh
 if multi:
  bh=14; c.setFillColor(Color(1,0.55,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,f">>> ENVIO CON {sum(x['qty'] for x in items)} PRODUCTOS <<<"); y-=bh
 n=len(items); hh=max(30,30+11*max(0,n-1))
 c.setFillColor(Color(1,0.95,0.55)); c.rect(0,y-hh,W,hh,fill=1,stroke=0)
 c.setStrokeColorRGB(0,0,0); c.line(0,y-hh,W,y-hh); c.setFillColorRGB(0,0,0)
 c.setFont("Helvetica",7); c.drawCentredString(W/2,y-9,f"[ROSA-MARIA/{tag}] Ship:{ship}")
 fs=10 if n<=3 else 9; c.setFont("Helvetica-Bold",fs); yy=y-9-11
 for it in items:
  # cantidad + modelo + color (todos vacíos permitidos, no inventar)
  parts=[str(it["qty"])]
  if it["modelo"]: parts.append(it["modelo"])
  if it["color"]: parts.append(it["color"])
  txt=" ".join(parts)
  if it["used"]: txt="USADO "+txt
  c.drawCentredString(W/2,yy,txt[:60]); yy-=11
 c.showPage(); c.save(); buf.seek(0); return PdfReader(buf).pages[0]

writer=PdfWriter(); manifest=[]; failed=[]
for x in selected:
 sid=x["shipment_id"]
 q=requests.get(f"{API}/shipment_labels",headers=H,params={"shipment_ids":sid,"response_type":"pdf","savePdf":"Y"},timeout=40)
 if q.status_code!=200 or "application/pdf" not in q.headers.get("content-type","").lower():
  failed.append({"shipment_id":sid,"http":q.status_code,"detail":q.text[:200]}); continue
 rdr=PdfReader(io.BytesIO(q.content))
 for p in rdr.pages:
  W=float(p.mediabox.width); Hh=float(p.mediabox.height)
  ov=overlay(W,Hh,sid,x["tag"],x["items"],x["used"],x["multi"],x["delayed"])
  m=PageObject.create_blank_page(width=W,height=Hh); m.merge_page(p); m.merge_page(ov)
  writer.add_page(m)
 manifest.append(x)
with open(OUT,"wb") as f: writer.write(f)
with open(MANI,"w") as f: json.dump({"generated_at":now.isoformat(),"seller":SELLER,"breakdown":dict(sub_stats),"delayed_count":delayed_count,"ready_to_print_count":r2p_count,"unique_shipments":len(manifest),"pages":len(writer.pages),"failed":failed,"shipments":manifest},f,indent=2,ensure_ascii=False)
print(f"OK {OUT} pages={len(writer.pages)} ship={len(manifest)} failed={len(failed)}")
