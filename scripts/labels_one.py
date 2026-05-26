"""Etiquetas pendientes de UNA cuenta (parametrizada via env ACCOUNT).
Usa la APP NUEVA 2008666770714005. Formato compacto en español + pack aggregation.
Output: ETIQUETAS_{ACCOUNT}.pdf
"""
import os, io, time, requests
from datetime import datetime, timedelta, timezone
from collections import Counter
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from pdf2image import convert_from_bytes
from PIL import ImageOps

APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]
ACCOUNT = os.environ["ACCOUNT"].strip()  # ej "Wilbert", "Yiriam", "Asva", etc.
RT_SECRET_NAME = os.environ.get("RT_SECRET_NAME") or f"MELI_REFRESH_TOKEN_{ACCOUNT.upper()}"
RT = os.environ.get(RT_SECRET_NAME)
if not RT:
    raise SystemExit(f"No hay token: {RT_SECRET_NAME}")
TZ = timezone(timedelta(hours=-6))
PAGE_W=4*72; PAGE_H=6*72
ALLOWED_SUBS = {"printed", "ready_to_print"}
# Filtros opcionales: lista separada por coma en EXCLUDE_TITLE_CONTAINS
EX_TITLE = set(s.strip().lower() for s in (os.environ.get("EXCLUDE_TITLE_CONTAINS","") or "").split(",") if s.strip())
EX_MODELS = set(s.strip() for s in (os.environ.get("EXCLUDE_MODELS","") or "").split(",") if s.strip())

def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

def _parse_color_map(text):
    if not text: return None
    tl=" "+text.lower()+" "
    cm=[("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
        ("aqua","Aqua"),("celeste","Celeste"),("negr","Negro"),(" black","Negro"),
        ("roj","Rojo"),(" red","Rojo"),("rosa","Rosa"),("pink","Rosa"),
        ("morad","Morado"),("violeta","Morado"),("purple","Morado"),
        (" azul","Azul"),(" blue","Azul"),("blanco","Blanco"),("white","Blanco"),
        ("verde","Verde"),("green","Verde"),("amarillo","Amarillo"),("yellow","Amarillo"),
        ("naranja","Naranja"),("orange","Naranja"),("gris","Gris"),("gray","Gris"),("grey","Gris"),
        ("plateado","Plata"),("silver","Plata"),("dorado","Dorado"),("gold","Dorado")]
    for k,v in cm:
        if k in tl: return v
    return None

def _norm(text):
    if not text: return None
    t=text.strip()
    for p in ["Color ","color "]:
        if t.startswith(p): t=t[len(p):]
    return t.title() if t else None

def get_variant_color(item_obj, H):
    for a in (item_obj.get("variation_attributes") or []):
        if a.get("id")=="COLOR" or "color" in (a.get("name","") or "").lower():
            vn=a.get("value_name") or ""
            return _parse_color_map(vn) or _norm(vn)
    iid=item_obj.get("id"); vid=item_obj.get("variation_id")
    if iid and vid:
        try:
            r=requests.get(f"https://api.mercadolibre.com/items/{iid}/variations/{vid}",headers=H,timeout=8)
            if r.status_code==200:
                for ac in (r.json().get("attribute_combinations") or []):
                    if ac.get("id")=="COLOR" or "color" in (ac.get("name","") or "").lower():
                        vn=ac.get("value_name") or ""
                        return _parse_color_map(vn) or _norm(vn)
        except: pass
    return None

def get_model(title):
    t=(title or "").strip(); tl_full=t.lower()
    for w in ["Bocina ","bocina ","Parlante ","parlante ","Altavoz ","altavoz ","Speaker ","speaker ",
              "JBL ","jbl ","Jbl ","Sony ","SONY ","Bose ","BOSE "]:
        t=t.replace(w,"")
    tl=t.lower()
    if "go 4" in tl or "go4" in tl: return "Go4"
    if "go 3" in tl or "go3" in tl: return "Go3"
    if "clip 5" in tl or "clip5" in tl: return "Clip5"
    if "charge 6" in tl or "charge6" in tl: return "Charge6"
    if "flip 7" in tl or "flip7" in tl: return "Flip7"
    if "grip" in tl: return "Grip"
    if "xb100" in tl: return "XB100"
    if "soundlink" in tl: return "SoundLink"
    if "modelo padrão" in tl_full or "modelo padrao" in tl_full or "padrão" in tl_full:
        return "JBL Impermeable"
    return t[:24]

def clean_title(item_obj, H):
    title=item_obj.get("title","")
    tl=title.lower()
    model=get_model(title)
    color=get_variant_color(item_obj,H) or _parse_color_map(title)
    base=f"{model} {color}" if color else model
    if "reacondicionado" in tl or "reacond" in tl: base=f"{base} (Reacond.)"
    return base, model

_CC={}
def get_condition(item_obj, H):
    c=item_obj.get("condition")
    if c: return c
    iid=item_obj.get("id")
    if not iid: return None
    if iid in _CC: return _CC[iid]
    try:
        r=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=8,params={"attributes":"condition"})
        if r.status_code==200:
            c=(r.json() or {}).get("condition")
            _CC[iid]=c; return c
    except: pass
    _CC[iid]=None; return None

def detect_bbox(pdf_bytes, pi=0):
    try:
        imgs=convert_from_bytes(pdf_bytes,dpi=72,first_page=pi+1,last_page=pi+1)
        if not imgs: return None
        img=imgs[0].convert("L")
        bw=img.point(lambda p:0 if p<245 else 255,mode="L")
        inv=ImageOps.invert(bw); bb=inv.getbbox()
        if not bb: return None
        x0,y0t,x1,y1t=bb; iw,ih=img.size
        m=2
        return (max(0,x0-m), max(0,ih-y1t-m), min(iw,x1-x0+2*m), min(ih,y1t-y0t+2*m))
    except: return None

def render_header(s, header_h):
    has_used=bool(s.get("has_used")); n_prods=s.get("n_prods",len(s.get("comp_lines",[])))
    multi=n_prods>1
    us=14 if has_used else 0; mu=14 if multi else 0
    total_h=header_h+us+mu
    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(PAGE_W,PAGE_H))
    cx=PAGE_W/2.0
    c.setFillColor(Color(1,0.96,0.74)); c.rect(0,PAGE_H-total_h,PAGE_W,header_h,fill=1,stroke=0)
    top=PAGE_H
    if has_used:
        c.setFillColorRGB(0.85,0.13,0.13); c.rect(0,top-us,PAGE_W,us,fill=1,stroke=0)
        c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9)
        c.drawCentredString(cx,top-11,"*** PRODUCTO USADO ***"); top-=us
    if multi:
        c.setFillColorRGB(0.90,0.49,0.13); c.rect(0,top-mu,PAGE_W,mu,fill=1,stroke=0)
        c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",9)
        c.drawCentredString(cx,top-11,f">>> ENVIO CON {n_prods} PRODUCTOS <<<"); top-=mu
    yt=top
    c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold",7.5)
    c.drawCentredString(cx,yt-11,f"[{s['account'].upper()}] {s['buyer'][:30]} | Ship:{s['sid']}")
    big=s["comp_lines"][:6]; n=len(big)
    fs,lh=(14,16) if n<=2 else (12,14) if n<=4 else (10,12)
    bt=yt-18; bb=PAGE_H-total_h+4
    bh=bt-bb; th=n*lh
    fy=bt-(bh-th)/2.0-fs*0.8
    c.setFont("Helvetica-Bold",fs)
    y=fy
    for line in big:
        c.drawCentredString(cx,y,line[:34]); y-=lh
    c.showPage(); c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]

# === FASE 1 ===
print(f"=== {ACCOUNT} (token={RT_SECRET_NAME}) ===")
at=tok(RT)
if not at: raise SystemExit("Token fail")
H={"Authorization":f"Bearer {at}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
uid=me.get("id"); print(f"  uid={uid}  nick={me.get('nickname')}")
NOW=datetime.now(timezone.utc); START=NOW-timedelta(days=180)
orders=[]; off=0
while True:
    r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,timeout=20,
        params={"seller":uid,"order.status":"paid",
                "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":off}).json()
    res=r.get("results",[])
    if not res: break
    orders.extend(res); off+=len(res)
    if off>=r.get("paging",{}).get("total",0): break
obs={}
for o in orders:
    sid=(o.get("shipping") or {}).get("id")
    if sid: obs.setdefault(sid,[]).append(o)
print(f"  shipping ids: {len(obs)}")
ships=[]
for sid, ord_list in obs.items():
    try:
        sh=requests.get(f"https://api.mercadolibre.com/shipments/{sid}",headers=H,timeout=10).json()
        st=sh.get("status"); sub=sh.get("substatus")
        if st!="ready_to_ship" or sub not in ALLOWED_SUBS: continue
        comp=[]; used=False; skip=False
        for ord_o in ord_list:
            for it in ord_o.get("order_items",[]):
                io_obj=it.get("item") or {}
                tcln,model=clean_title(io_obj,H)
                if model in EX_MODELS: skip=True
                rt=(io_obj.get("title") or "").lower(); rcln=tcln.lower()
                if any(kw in rt or kw in rcln for kw in EX_TITLE): skip=True
                qty=it.get("quantity",1); iid=io_obj.get("id") or ""
                cond=get_condition(io_obj,H)
                if cond=="used":
                    used=True; comp.append(f"USADO {qty} {tcln}")
                else:
                    comp.append(f"{qty} {tcln}")
        if skip: continue
        buyer=(ord_list[0].get("buyer") or {}).get("nickname","?")
        ships.append({"sid":sid,"account":ACCOUNT,"buyer":buyer,"comp_lines":comp,
                      "has_used":used,"n_prods":len(comp),"substatus":sub})
        time.sleep(0.04)
    except Exception as e:
        print(f"  err {sid}: {str(e)[:80]}")
print(f"  seleccionados: {len(ships)}")
multi=[s for s in ships if s["n_prods"]>1]
if multi:
    print(f"  envíos multi-producto: {len(multi)}")
    for s in multi: print(f"    sid={s['sid']} ({s['n_prods']} prods): {' + '.join(s['comp_lines'])}")
ships.sort(key=lambda s:(0 if s["has_used"] else 1,"/".join(s["comp_lines"]),s["sid"]))

# === FASE 2 ===
writer=PdfWriter(); fail=[]
for s in ships:
    try:
        r=requests.get("https://api.mercadolibre.com/shipment_labels",headers=H,
            params={"shipment_ids":s["sid"],"response_type":"pdf"},timeout=30)
        if r.status_code!=200 or not r.headers.get("content-type","").lower().startswith("application/pdf"):
            fail.append(s["sid"]); continue
        raw=r.content; lp=PdfReader(io.BytesIO(raw))
        for pi,page in enumerate(lp.pages):
            box=page.cropbox if page.cropbox else page.mediabox
            lx0=float(box.left); ly0=float(box.bottom); lw=float(box.width); lh=float(box.height)
            bb=detect_bbox(raw,pi)
            if bb:
                cx0,cy0,cw,ch=bb
                lx0=float(box.left)+float(cx0); ly0=float(box.bottom)+float(cy0); lw=float(cw); lh=float(ch)
            nl=min(len(s["comp_lines"]),6); header_h=22+nl*15
            la=PAGE_H-header_h
            np_=PageObject.create_blank_page(width=PAGE_W,height=PAGE_H)
            sx=PAGE_W/lw; sy=la/lh
            op=Transformation().translate(-lx0,-ly0).scale(sx,sy)
            np_.merge_transformed_page(page,op)
            np_.merge_page(render_header(s,header_h))
            writer.add_page(np_)
    except Exception as e:
        fail.append(s["sid"])
    time.sleep(0.08)
out=f"ETIQUETAS_{ACCOUNT.upper()}.pdf"
with open(out,"wb") as f: writer.write(f)
print(f"\n✅ PDF: {out} ({len(writer.pages)} págs) | Fallidas: {len(fail)}")
print("Top productos:")
for p,n in Counter("/".join(s["comp_lines"]) for s in ships).most_common(10): print(f"  {n:3} {p}")
