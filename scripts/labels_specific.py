"""ETIQUETAS específicas — recibe ORDERS env var (formato: 'Cuenta:ORDER_ID,Cuenta:ORDER_ID,...').
Construye PDF 4x6 con el mismo header amarillo + USADO si aplica.
"""
import os, io, time, requests
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from pdf2image import convert_from_bytes
from PIL import ImageOps

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCS={
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Wilbert":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "Yc_New":   os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}
PAGE_W=4*72; PAGE_H=6*72

def tok(rt):
    if not rt: return None
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

_COND_CACHE={}
def get_condition(item_obj, H):
    cond = item_obj.get("condition")
    if cond: return cond
    iid = item_obj.get("id")
    if not iid: return None
    if iid in _COND_CACHE: return _COND_CACHE[iid]
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                         headers=H, timeout=8, params={"attributes":"condition"})
        if r.status_code == 200:
            cond = (r.json() or {}).get("condition")
            _COND_CACHE[iid]=cond; return cond
    except: pass
    _COND_CACHE[iid]=None; return None

def detect_content_bbox(pdf_bytes, page_idx=0):
    try:
        imgs = convert_from_bytes(pdf_bytes, dpi=72,
                                  first_page=page_idx+1, last_page=page_idx+1)
        if not imgs: return None
        img = imgs[0].convert("L")
        bw = img.point(lambda p: 0 if p < 245 else 255, mode="L")
        inv = ImageOps.invert(bw)
        bbox = inv.getbbox()
        if not bbox: return None
        x0, y0_top, x1, y1_top = bbox
        img_w, img_h = img.size
        pdf_y0 = img_h - y1_top
        pdf_y1 = img_h - y0_top
        m = 2
        return (max(0, x0-m), max(0, pdf_y0-m),
                min(img_w, x1-x0+2*m), min(img_h, pdf_y1-pdf_y0+2*m))
    except: return None

def render_header(s, header_h):
    has_used = bool(s.get("has_used"))
    usado_strip = 14 if has_used else 0
    total_h = header_h + usado_strip
    buf=io.BytesIO()
    c=canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    cx = PAGE_W/2.0
    c.setFillColor(Color(1, 0.96, 0.74))
    c.rect(0, PAGE_H-total_h, PAGE_W, header_h, fill=1, stroke=0)
    if has_used:
        c.setFillColorRGB(0.85, 0.13, 0.13)
        c.rect(0, PAGE_H-usado_strip, PAGE_W, usado_strip, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, PAGE_H-11, "*** PRODUCTO USADO ***")
    yellow_top = PAGE_H - usado_strip
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(cx, yellow_top-11, f"[{s['account'].upper()}] {s['buyer'][:30]} | Ship:{s['sid']}")
    big = s["comp_lines"][:4]; n=len(big); lh=16
    block_top=yellow_top-18; block_bot=PAGE_H-total_h+4
    block_h=block_top-block_bot; text_h=n*lh
    first_y = block_top - (block_h - text_h)/2.0 - 12
    c.setFont("Helvetica-Bold", 14)
    y=first_y
    for line in big:
        c.drawCentredString(cx, y, line[:30]); y-=lh
    c.showPage(); c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# Parse ORDERS env: "Cuenta:OID,Cuenta:OID,..."
ORDERS_RAW = os.environ.get("ORDERS","").strip()
if not ORDERS_RAW:
    raise SystemExit("ORDERS env var vacía. Formato: 'Claribel:2000012780394633,Raymundo:2000012775293605'")
targets=[]
for chunk in ORDERS_RAW.split(","):
    chunk = chunk.strip()
    if not chunk: continue
    acc, oid = chunk.split(":",1)
    targets.append((acc.strip(), oid.strip()))
print(f"=== Targets: {targets} ===")

writer = PdfWriter()
fail = []
ok = 0
for acc, oid in targets:
    rt = ACCS.get(acc)
    if not rt:
        print(f"  err {acc}/{oid}: cuenta sin token"); fail.append((acc,oid,"sin token")); continue
    at = tok(rt)
    if not at:
        print(f"  err {acc}/{oid}: no pude renovar token"); fail.append((acc,oid,"refresh token failed")); continue
    H = {"Authorization": f"Bearer {at}"}

    # Fetch order
    o = requests.get(f"https://api.mercadolibre.com/orders/{oid}", headers=H, timeout=15).json()
    sid = (o.get("shipping") or {}).get("id")
    if not sid:
        print(f"  err {acc}/{oid}: sin shipping_id en order")
        fail.append((acc,oid,"sin shipping")); continue

    # Build comp_lines + has_used
    items = o.get("order_items",[])
    comp_lines=[]; has_used=False
    for it in items:
        io_obj = it.get("item") or {}
        title = clean_title(io_obj.get("title",""))
        qty = it.get("quantity",1)
        cond = get_condition(io_obj, H)
        if cond == "used":
            has_used = True
            comp_lines.append(f"USADO {title} x{qty}")
        else:
            comp_lines.append(f"{title} x{qty}")
    buyer = (o.get("buyer") or {}).get("nickname","?")
    s = {"sid":sid,"account":acc,"buyer":buyer,"comp_lines":comp_lines,"has_used":has_used}
    print(f"  {acc}/{oid} -> sid={sid}  buyer={buyer}  used={has_used}  comp={comp_lines}")

    # Get label PDF
    r = requests.get("https://api.mercadolibre.com/shipment_labels",
                    headers=H, params={"shipment_ids":sid,"response_type":"pdf"}, timeout=30)
    if r.status_code!=200 or not r.headers.get("content-type","").lower().startswith("application/pdf"):
        msg = f"HTTP {r.status_code} {r.text[:200]}"
        print(f"  err {acc}/{oid}: {msg}")
        fail.append((acc,oid,msg)); continue
    raw = r.content
    lbl_pdf = PdfReader(io.BytesIO(raw))
    for pidx, label_page in enumerate(lbl_pdf.pages):
        box = label_page.cropbox if label_page.cropbox else label_page.mediabox
        lbl_x0=float(box.left); lbl_y0=float(box.bottom)
        lbl_w=float(box.width); lbl_h=float(box.height)
        cb = detect_content_bbox(raw, pidx)
        if cb:
            cx0,cy0,cw,ch = cb
            lbl_x0=float(box.left)+float(cx0)
            lbl_y0=float(box.bottom)+float(cy0)
            lbl_w=float(cw); lbl_h=float(ch)
        n_lines=min(len(comp_lines),4)
        header_h = 22 + n_lines*16
        label_area_h = PAGE_H - header_h
        new_page = PageObject.create_blank_page(width=PAGE_W, height=PAGE_H)
        sx = PAGE_W/lbl_w; sy = label_area_h/lbl_h
        op = (Transformation()
              .translate(-lbl_x0, -lbl_y0)
              .scale(sx, sy))
        new_page.merge_transformed_page(label_page, op)
        new_page.merge_page(render_header(s, header_h))
        writer.add_page(new_page)
        ok += 1

with open("ETIQUETAS_ESPECIFICAS.pdf","wb") as f: writer.write(f)
print(f"\n✅ PDF: ETIQUETAS_ESPECIFICAS.pdf ({ok} págs) | Fallidas: {len(fail)}")
for f_ in fail:
    print(f"   FALLIDA acc={f_[0]} order={f_[1]} → {f_[2][:200]}")
