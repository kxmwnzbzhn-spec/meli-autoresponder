#!/usr/bin/env python3
import os, io, json, re, requests
from collections import OrderedDict, Counter
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
API="https://api.mercadolibre.com"; SELLER=3446873427
OUT="ETIQUETAS_ALEJANDRA_DAYANA.pdf"; MANI="MANIFEST_ALEJANDRA_DAYANA.json"

# --- Auth: intenta APP_ID luego APP_ID_NEW ---
rt=os.environ["MELI_REFRESH_TOKEN_ALEJANDRA_DAYANA"]
tok=None
for app_e,sec_e in [("MELI_APP_ID","MELI_APP_SECRET"),("MELI_APP_ID_NEW","MELI_APP_SECRET_NEW")]:
 app=os.environ.get(app_e); sec=os.environ.get(sec_e)
 if not app or not sec: continue
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":app,"client_secret":sec,"refresh_token":rt},timeout=30)
 if r.status_code==200:
  tok=r.json(); print(f"[auth] OK con {app_e}"); break
 else:
  print(f"[auth] {app_e} → {r.status_code} {r.text[:200]}")
if not tok: raise SystemExit("no se pudo autenticar")
with open("/tmp/rot_dayana","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print(f"[me] uid={me.get('id')} nick={me.get('nickname')}")
if int(me.get("id") or 0)!=SELLER:
 SELLER=int(me.get("id"))  # ajusta al real de la cuenta

MODEL_RULES=[
 (r"\bgo\s*5\b","Go5"),(r"\bgo\s*4\b","Go4"),(r"\bgo\s*3\b","Go3"),
 (r"\bclip\s*5\b","Clip5"),(r"\bclip\s*4\b","Clip4"),
 (r"\bcharge\s*essential\s*2\b","Charge Essential 2"),(r"\bcharge\s*6\b","Charge6"),(r"\bcharge\s*5\b","Charge5"),
 (r"\bflip\s*essential\s*2\b","Flip Essential 2"),(r"\bflip\s*7\b","Flip7"),(r"\bflip\s*6\b","Flip6"),
 (r"\bxtreme\s*4\b","Xtreme4"),(r"\bxtreme\s*3\b","Xtreme3"),
 (r"\bpartybox\b[^\d]*(\d+)?",None),(r"\bboombox\s*3\b","Boombox3"),(r"\bpulse\s*5\b","Pulse5"),(r"\btuner\s*xl\b","Tuner XL"),
 (r"\bemberton\s*ii\b","Emberton II"),(r"\bemberton\b","Emberton"),(r"\bwillen\b","Willen"),(r"\bmiddleton\b","Middleton"),
 (r"\bstanmore\s*iii\b","Stanmore III"),(r"\bkilburn\s*ii\b","Kilburn II"),
 (r"\bpill\b","Pill"),(r"\bstudio\s*pro\b","Studio Pro"),(r"\bsolo\s*4\b","Solo 4"),(r"\bfit\s*pro\b","Fit Pro"),
 (r"\bsrs-?xb\s*100\b","XB100"),(r"\bsrs-?xb\s*13\b","XB13"),(r"\bsrs-?xb\s*23\b","XB23"),(r"\bsrs-?xb\s*43\b","XB43"),
 (r"\bult\s*field\s*7\b","ULT Field 7"),(r"\bult\s*field\s*1\b","ULT Field 1"),
 (r"\bsoundlink\s*micro\b","SoundLink Micro"),(r"\bsoundlink\s*flex\b","SoundLink Flex"),(r"\bsoundlink\s*mini\s*ii\b","SoundLink Mini II"),(r"\bsoundlink\b","SoundLink"),
]
BR=re.compile(r"\b(jbl|beats|marshall|sony|bose|ue|ultimate\s*ears)\b",re.I)
BC=re.compile(r"\b(bocina|parlante|altavoz|speaker|bluetooth|portatil|portátil|inalambric[oa]|inalámbric[oa])\b",re.I)
COLOR_TR={"Preto":"Negro","Preta":"Negro","Vermelho":"Rojo","Azul Escuro":"Azul Oscuro","Azul Marinho":"Azul Marino","Branco":"Blanco","Amarelo":"Amarillo","Cinza":"Gris"}
def clean_color(v):
 if not v: return ""
 v=v.strip()
 for k,val in COLOR_TR.items():
  if v.lower()==k.lower(): return val
 return v.title() if v.islower() else v
def derive_model(title):
 t=title.lower()
 for rx,canon in MODEL_RULES:
  m=re.search(rx,t)
  if m:
   if canon: return canon
   g=m.group(1) if m.groups() else None
   return "Partybox"+(" "+g if g else "")
 t2=BC.sub(" ",BR.sub(" ",title))
 t2=re.sub(r"[^A-Za-z0-9\s]"," ",t2)
 t2=re.sub(r"\s+"," ",t2).strip()
 return " ".join(t2.split()[:3]) or "Producto"
def derive_color(line):
 for a in (line.get("variation_attributes") or []):
  if (a.get("id") or "").upper()=="COLOR" or "color" in (a.get("name") or "").lower():
   v=clean_color(a.get("value_name"))
   if v: return v
 item=line.get("item") or {}
 iid=item.get("id"); vid=item.get("variation_id")
 if iid and vid:
  try:
   g=requests.get(f"{API}/items/{iid}/variations/{vid}",headers=H,timeout=15)
   if g.status_code==200:
    for a in (g.json().get("attribute_combinations") or []):
     if (a.get("id") or "").upper()=="COLOR":
      v=clean_color(a.get("value_name"))
      if v: return v
  except Exception: pass
 title=(item.get("title") or "").lower()
 for col in ["negro mate","azul oscuro","azul marino","rojo audaz","negro","blanco","azul","rojo","rosa","verde","amarillo","gris","dorado","plata","morado","celeste","naranja"]:
  if col in title: return clean_color(col.capitalize())
 return ""
COND={}
def cond_of(iid):
 if iid in COND: return COND[iid]
 c="new"
 try:
  g=requests.get(f"{API}/items/{iid}?attributes=condition",headers=H,timeout=15)
  if g.status_code==200: c=g.json().get("condition") or "new"
 except Exception: pass
 COND[iid]=c; return c

now=datetime.now(timezone.utc); start=now-timedelta(days=60)
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
sub_stats=Counter(); selected=[]
for sid,rows in by_sid.items():
 q=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=20)
 if q.status_code!=200: continue
 sh=q.json()
 if sh.get("status")!="ready_to_ship": continue
 sub=sh.get("substatus"); sub_stats[sub]+=1
 if sub not in {"ready_to_print","printed"}: continue
 items=[]; any_used=False
 for order in rows:
  for line in order.get("order_items") or []:
   obj=line.get("item") or {}
   title=(obj.get("title") or "").strip()
   qty=int(line.get("quantity") or 0)
   iid=obj.get("id") or ""
   cnd=cond_of(iid) if iid else "new"
   if cnd=="used": any_used=True
   items.append({"qty":qty,"modelo":derive_model(title),"color":derive_color(line),"used":cnd=="used","item_id":iid,"title":title})
 merged=OrderedDict()
 for x in items:
  k=(x["modelo"],x["color"],x["used"])
  if k in merged: merged[k]["qty"]+=x["qty"]
  else: merged[k]=dict(x)
 selected.append({"shipment_id":sid,"substatus":sub,"order_ids":[str(o.get("id")) for o in rows],"items":list(merged.values()),"used":any_used,"multi":sum(x["qty"] for x in merged.values())>=2 and len(merged)>=2})
selected.sort(key=lambda x:int(x["shipment_id"]))
print(f"[stats] substatus_breakdown={dict(sub_stats)}")
print(f"[stats] seleccionadas(ready_to_print+printed)={len(selected)}")

def overlay(W,Hh,ship,items,used,multi):
 buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(W,Hh))
 y=Hh
 if used:
  bh=14; c.setFillColor(Color(0.85,0.1,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,"*** PRODUCTO USADO ***"); y-=bh
 if multi:
  bh=14; c.setFillColor(Color(1,0.55,0.1)); c.rect(0,y-bh,W,bh,fill=1,stroke=0)
  c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold",9); c.drawCentredString(W/2,y-10,f">>> ENVIO CON {sum(x['qty'] for x in items)} PRODUCTOS <<<"); y-=bh
 n=len(items); hh=max(30,30+11*max(0,n-1))
 c.setFillColor(Color(1,0.95,0.55)); c.rect(0,y-hh,W,hh,fill=1,stroke=0)
 c.setStrokeColorRGB(0,0,0); c.line(0,y-hh,W,y-hh); c.setFillColorRGB(0,0,0)
 c.setFont("Helvetica",7); c.drawCentredString(W/2,y-9,f"[ALE-DAYANA] Ship:{ship}")
 fs=10 if n<=3 else 9; c.setFont("Helvetica-Bold",fs); yy=y-9-11
 for it in items:
  txt=f"{it['qty']} {it['modelo']}{(' '+it['color']) if it['color'] else ''}".strip()
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
  ov=overlay(W,Hh,sid,x["items"],x["used"],x["multi"])
  m=PageObject.create_blank_page(width=W,height=Hh); m.merge_page(p); m.merge_page(ov)
  writer.add_page(m)
 manifest.append({k:v for k,v in x.items() if k!="H"})
with open(OUT,"wb") as f: writer.write(f)
with open(MANI,"w") as f: json.dump({"generated_at":now.isoformat(),"seller":SELLER,"nickname":me.get('nickname'),"breakdown":dict(sub_stats),"unique_shipments":len(manifest),"pages":len(writer.pages),"failed":failed,"shipments":manifest},f,indent=2,ensure_ascii=False)
print(f"OK {OUT} pages={len(writer.pages)} ship={len(manifest)} failed={len(failed)}")
