"""Etiquetas LUNES con OVERLAY de producto en LA MISMA pagina (no antes).
Producto sin marca JBL. Ejemplo: 'Go 4 Azul x1' en lugar de 'JBL Go 4 Azul x1'.
"""
import os, io, time, re, requests
from datetime import datetime, timedelta, timezone
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
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
    """Quita 'JBL', 'Bocina', 'Parlante', etc. y deja solo modelo+color simple."""
    t = title
    # Remover marcas/genericos
    for w in ["Bocina ","Parlante ","Altavoz ","Speaker ","JBL ","jbl ","Sony ","Bose "]:
        t = t.replace(w, "")
    # Detectar modelo + color simple
    tl = t.lower()
    if "go 4" in tl or "go4" in tl: model = "Go 4"
    elif "go 3" in tl or "go3" in tl: model = "Go 3"
    elif "clip 5" in tl or "clip5" in tl: model = "Clip 5"
    elif "charge 6" in tl or "charge6" in tl: model = "Charge 6"
    elif "flip 7" in tl or "flip7" in tl: model = "Flip 7"
    elif "grip" in tl: model = "Grip"
    elif "xb100" in tl or "sony" in tl: model = "Sony XB100"
    elif "soundlink" in tl or "bose" in tl: model = "Bose SoundLink"
    else: model = t[:25]
    # Color
    col_map = [("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
               ("aqua","Aqua"),("celeste","Celeste"),("negr","Negro"),("black","Negro"),
               ("roj","Rojo"),("rosa","Rosa"),("pink","Rosa"),
               ("morad","Morado"),("violeta","Morado"),("purple","Morado"),
               ("azul","Azul"),("blue","Azul")]
    color = None
    for k,v in col_map:
        if k in tl:
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


def make_overlay(s):
    """Genera un PDF de 1 pagina con el header del producto en la parte superior."""
    buf=io.BytesIO()
    c=canvas.Canvas(buf, pagesize=letter)
    W, Hh = letter
    # rectangulo amarillo arriba
    c.setFillColor(Color(1, 0.96, 0.74))  # amarillo claro
    box_h = 28*mm + len(s["comp_lines"])*9*mm
    c.rect(0, Hh-box_h, W, box_h, fill=1, stroke=0)
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(8*mm, Hh-9*mm, f"[{s['account'].upper()}] {s['buyer'][:40]} | Ship:{s['sid']}")
    c.setFont("Helvetica-Bold", 16)
    y = Hh-19*mm
    for line in s["comp_lines"]:
        c.drawString(8*mm, y, line)
        y -= 9*mm
    c.showPage(); c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# === FASE 2: descargar etiquetas + overlay header ===
print("\n=== Generando PDF con OVERLAY en cada etiqueta ===")
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
            if r.status_code==200 and r.headers.get("content-type","").lower().startswith("application/pdf"):
                lbl_pdf=PdfReader(io.BytesIO(r.content))
                overlay_page = make_overlay(s)
                # Para cada pagina del label, mergear el overlay encima
                for page in lbl_pdf.pages:
                    page.merge_page(overlay_page)
                    writer.add_page(page)
            else:
                fail.append(s["sid"])
        except Exception as e:
            fail.append(s["sid"])
            print(f"    err {s['sid']}: {str(e)[:60]}")
        time.sleep(0.08)

out="ETIQUETAS_LUNES_PRODUCTO_EN_ETIQUETA.pdf"
with open(out,"wb") as f: writer.write(f)
print(f"\n✅ PDF: {out} ({len(writer.pages)} páginas) — overlay producto en cada etiqueta")
print(f"  Fallidas: {len(fail)}")
