"""V4: Header integrado en la MISMA pagina del label, mismo ancho.
Extiende la pagina hacia arriba para meter el header. Producto SIN marca.
"""
import os, io, time, requests
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCS={
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
}
TZ=timezone(timedelta(hours=-6))
LIMIT=datetime.fromisoformat("2026-05-04").replace(hour=23,minute=59,tzinfo=TZ)


def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")


def clean_title(title):
    t=(title or "").strip()
    for w in ["Bocina ","bocina ","Parlante ","parlante ","Altavoz ","altavoz ","Speaker ","speaker ",
              "JBL ","jbl ","Jbl ","Sony ","SONY ","Bose ","BOSE "]:
        t=t.replace(w,"")
    tl=t.lower()
    if "go 4" in tl or "go4" in tl: model="Go 4"
    elif "go 3" in tl or "go3" in tl: model="Go 3"
    elif "clip 5" in tl or "clip5" in tl: model="Clip 5"
    elif "charge 6" in tl or "charge6" in tl: model="Charge 6"
    elif "flip 7" in tl or "flip7" in tl: model="Flip 7"
    elif "grip" in tl: model="Grip"
    elif "xb100" in tl: model="Sony XB100"
    elif "soundlink" in tl: model="Bose SoundLink"
    else: model=t[:30]
    col_map=[("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
             ("aqua","Aqua"),("celeste","Celeste"),("negr","Negro"),("black","Negro"),
             ("roj","Rojo"),(" red","Rojo"),("rosa","Rosa"),("pink","Rosa"),
             ("morad","Morado"),("violeta","Morado"),("purple","Morado"),
             (" azul","Azul"),(" blue","Azul")]
    color=None
    for k,v in col_map:
        if k in (" "+tl):
            color=v; break
    return f"{model} {color}" if color else model


# === FASE 1: shipments ===
NOW=datetime.now(timezone.utc); START=NOW-timedelta(days=10)
shipments=[]
for acc, rt in ACCS.items():
    if not rt: continue
    print(f"=== {acc} ===")
    at=tok(rt)
    if not at: continue
    H={"Authorization":f"Bearer {at}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
    uid=me.get("id")
    if not uid: continue
    orders=[]; offset=0
    while True:
        r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,timeout=20,
            params={"seller":uid,"order.status":"paid",
                    "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":offset}).json()
        res=r.get("results",[])
        if not res: break
        orders.extend(res); offset+=len(res)
        if offset>=r.get("paging",{}).get("total",0): break
    obs={}
    for o in orders:
        sid=(o.get("shipping") or {}).get("id")
        if sid: obs[sid]=o
    matches=0
    for sid, ord_o in obs.items():
        try:
            sh=requests.get(f"https://api.mercadolibre.com/shipments/{sid}",headers=H,timeout=10).json()
            st=sh.get("status"); sub=sh.get("substatus")
            if st not in ("ready_to_ship","handling"): continue
            if sub in ("shipped","ready_to_pickup"): continue
            deadline=None
            try:
                sla=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/sla",headers=H,timeout=8).json()
                ed=sla.get("expected_date")
                if ed: deadline=datetime.fromisoformat(ed.replace("Z","+00:00")).astimezone(TZ)
            except: pass
            if not deadline:
                hist=sh.get("status_history") or {}
                dh=hist.get("date_handling")
                if dh: deadline=(datetime.fromisoformat(dh.replace("Z","+00:00"))+timedelta(hours=48)).astimezone(TZ)
            if not deadline or deadline>LIMIT: continue
            items=ord_o.get("order_items",[])
            comp_lines=[f"{clean_title((it.get('item') or {}).get('title',''))} x{it.get('quantity',1)}" for it in items]
            buyer=(ord_o.get("buyer") or {}).get("nickname","?")
            shipments.append({"sid":sid,"account":acc,"token":at,"comp_lines":comp_lines,"buyer":buyer})
            matches+=1
            time.sleep(0.04)
        except Exception as e:
            print(f"  err {sid}: {str(e)[:60]}")
    print(f"  matches: {matches}")

print(f"\nTotal: {len(shipments)} shipments")
shipments.sort(key=lambda s: ("/".join(s["comp_lines"]), s["account"]))


# === FASE 2: extender pagina del label hacia arriba con header ===
print("\n=== Generando PDF V4 ===")
from collections import defaultdict
by_acc=defaultdict(list)
for s in shipments:
    by_acc[s["account"]].append(s)

writer=PdfWriter()
fail=[]

for acc, ships in by_acc.items():
    if not ships: continue
    token=ships[0]["token"]
    H={"Authorization":f"Bearer {token}"}
    print(f"  {acc}: {len(ships)}")
    for s in ships:
        try:
            r=requests.get("https://api.mercadolibre.com/shipment_labels",
                          headers=H, params={"shipment_ids":s["sid"],"response_type":"pdf"},
                          timeout=30)
            if r.status_code!=200 or not r.headers.get("content-type","").lower().startswith("application/pdf"):
                fail.append(s["sid"]); continue
            lbl_pdf=PdfReader(io.BytesIO(r.content))
            for label_page in lbl_pdf.pages:
                # Dimensiones originales
                lbl_w = float(label_page.mediabox.width)
                lbl_h = float(label_page.mediabox.height)
                # Espacio extra para header (proporcional al alto del label)
                # ~12% del alto + suficiente para 1-3 lineas de producto
                n_lines = len(s["comp_lines"])
                hdr_h = 60 + n_lines*20  # puntos
                new_h = lbl_h + hdr_h

                # Crear nueva pagina con misma anchura + alto extendido
                new_page = PageObject.create_blank_page(width=lbl_w, height=new_h)

                # Generar header con reportlab a las dimensiones exactas
                buf=io.BytesIO()
                c=canvas.Canvas(buf, pagesize=(lbl_w, new_h))
                # Box amarillo en la parte superior (de altura hdr_h)
                c.setFillColor(Color(1, 0.96, 0.74))
                c.rect(0, lbl_h, lbl_w, hdr_h, fill=1, stroke=0)
                # Texto: cuenta + ship en 1ra linea (mas pequeno)
                c.setFillColorRGB(0,0,0)
                c.setFont("Helvetica-Bold", 11)
                head_line = f"[{s['account'].upper()}] {s['buyer'][:25]} | Ship:{s['sid']}"
                c.drawString(8, lbl_h + hdr_h - 18, head_line[:65])
                # Producto SIN MARCA (grande y bold)
                c.setFont("Helvetica-Bold", 18)
                y = lbl_h + hdr_h - 42
                for line in s["comp_lines"][:5]:
                    c.drawString(8, y, line)
                    y -= 20
                c.showPage(); c.save()
                buf.seek(0)
                hdr_page = PdfReader(buf).pages[0]

                # Mergear header (full size) en new_page
                new_page.merge_page(hdr_page)
                # Mergear el label original en su posicion natural (origen 0,0 = bottom-left)
                new_page.merge_page(label_page)

                writer.add_page(new_page)
        except Exception as e:
            fail.append(s["sid"])
            print(f"    err {s['sid']}: {str(e)[:80]}")
        time.sleep(0.08)

out="ETIQUETAS_LUNES_V4.pdf"
with open(out,"wb") as f: writer.write(f)
print(f"\n✅ PDF: {out} ({len(writer.pages)} páginas)")
print(f"  Fallidas: {len(fail)}")
