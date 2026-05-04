"""V3: Header AMARILLO con producto SIN MARCA en la parte superior de cada etiqueta.
Usa PageObject.merge_translated_page para colocar el label DEBAJO del header.
"""
import os, io, time, requests
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from pypdf.generic import RectangleObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
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
    """Quita marcas y deja modelo+color simple."""
    t = (title or "").strip()
    for w in ["Bocina ","bocina ","Parlante ","parlante ","Altavoz ","altavoz ","Speaker ","speaker ",
              "JBL ","jbl ","Jbl ","Sony ","SONY ","Bose ","BOSE "]:
        t = t.replace(w, "")
    tl = t.lower()
    if "go 4" in tl or "go4" in tl: model = "Go 4"
    elif "go 3" in tl or "go3" in tl: model = "Go 3"
    elif "clip 5" in tl or "clip5" in tl: model = "Clip 5"
    elif "charge 6" in tl or "charge6" in tl: model = "Charge 6"
    elif "flip 7" in tl or "flip7" in tl: model = "Flip 7"
    elif "grip" in tl: model = "Grip"
    elif "xb100" in tl: model = "Sony XB100"
    elif "soundlink" in tl: model = "Bose SoundLink"
    else: model = t[:30]
    col_map = [("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
               ("aqua","Aqua"),("celeste","Celeste"),("negr","Negro"),("black","Negro"),
               ("roj","Rojo"),(" red","Rojo"),("rosa","Rosa"),("pink","Rosa"),
               ("morad","Morado"),("violeta","Morado"),("purple","Morado"),
               (" azul","Azul"),(" blue","Azul")]
    color = None
    for k,v in col_map:
        if k in (" "+tl):
            color = v
            break
    return f"{model} {color}" if color else model


# === FASE 1: shipments con productos ===
NOW=datetime.now(timezone.utc)
START=NOW-timedelta(days=10)
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
            shipments.append({"sid":sid,"account":acc,"token":at,
                              "comp_lines":comp_lines,"buyer":buyer})
            matches+=1
            time.sleep(0.04)
        except Exception as e:
            print(f"  err {sid}: {str(e)[:60]}")
    print(f"  matches: {matches}")

print(f"\nTotal: {len(shipments)} shipments")
shipments.sort(key=lambda s: ("/".join(s["comp_lines"]), s["account"]))


# === FASE 2: descargar etiquetas + componer pagina nueva con header arriba + label abajo ===
print("\n=== Generando PDF V3 ===")

PAGE_W, PAGE_H = letter  # 612 x 792
HEADER_H = 100  # puntos (~ 35mm) reservados para el header arriba

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
                # Crear NUEVA pagina letter
                new_page = PageObject.create_blank_page(width=PAGE_W, height=PAGE_H)

                # Dibujar header amarillo en el TOP usando reportlab
                buf=io.BytesIO()
                c=canvas.Canvas(buf, pagesize=letter)
                # Box amarillo en top
                box_h = HEADER_H
                c.setFillColor(Color(1, 0.96, 0.74))
                c.rect(0, PAGE_H - box_h, PAGE_W, box_h, fill=1, stroke=0)
                # Texto
                c.setFillColorRGB(0,0,0)
                c.setFont("Helvetica-Bold", 11)
                c.drawString(8, PAGE_H - 18, f"[{s['account'].upper()}] {s['buyer'][:35]} | Ship:{s['sid']}")
                c.setFont("Helvetica-Bold", 18)
                y = PAGE_H - 42
                for line in s["comp_lines"][:5]:
                    c.drawString(8, y, line)
                    y -= 18
                c.showPage(); c.save()
                buf.seek(0)
                hdr_page = PdfReader(buf).pages[0]

                # Merge header onto new page (header está full letter)
                new_page.merge_page(hdr_page)

                # Escalar y posicionar la etiqueta original DEBAJO del header
                lbl_box = label_page.mediabox
                lbl_w = float(lbl_box.width)
                lbl_h = float(lbl_box.height)
                # Espacio disponible debajo del header
                avail_w = PAGE_W - 20  # margen
                avail_h = PAGE_H - HEADER_H - 20
                scale = min(avail_w/lbl_w, avail_h/lbl_h)
                # Centrar horizontal, top justify (debajo header)
                tx = (PAGE_W - lbl_w*scale) / 2
                ty = PAGE_H - HEADER_H - lbl_h*scale - 10
                trans = Transformation().scale(scale, scale).translate(tx, ty)
                new_page.merge_transformed_page(label_page, trans)

                writer.add_page(new_page)
        except Exception as e:
            fail.append(s["sid"])
            print(f"    err {s['sid']}: {str(e)[:80]}")
        time.sleep(0.08)

out="ETIQUETAS_LUNES_V3.pdf"
with open(out,"wb") as f: writer.write(f)
print(f"\n✅ PDF: {out} ({len(writer.pages)} páginas)")
print(f"  Fallidas: {len(fail)}")
