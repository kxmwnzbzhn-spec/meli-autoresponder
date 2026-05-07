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

def _parse_color(text):
    if not text: return None
    tl=" "+text.lower()+" "
    col_map=[("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
             ("aqua","Aqua"),("celeste","Celeste"),("negr","Negro"),(" black","Negro"),
             ("roj","Rojo"),(" red","Rojo"),("rosa","Rosa"),("pink","Rosa"),
             ("morad","Morado"),("violeta","Morado"),("purple","Morado"),
             (" azul","Azul"),(" blue","Azul"),("blanco","Blanco"),("white","Blanco"),
             ("verde","Verde"),("green","Verde"),("amarillo","Amarillo"),("yellow","Amarillo"),
             ("naranja","Naranja"),("orange","Naranja"),("gris","Gris"),("gray","Gris"),
             ("plateado","Plata"),("silver","Plata"),("dorado","Dorado"),("gold","Dorado")]
    for k,v in col_map:
        if k in tl: return v
    return None

def get_variant_color(item_obj, H):
    attrs = item_obj.get("variation_attributes") or []
    for a in attrs:
        if a.get("id")=="COLOR" or "color" in (a.get("name","") or "").lower():
            v = a.get("value_name") or ""
            c = _parse_color(v)
            if c: return c
    iid = item_obj.get("id"); vid = item_obj.get("variation_id")
    if iid and vid:
        try:
            r = requests.get(f"https://api.mercadolibre.com/items/{iid}/variations/{vid}",
                             headers=H, timeout=8)
            if r.status_code == 200:
                for ac in (r.json().get("attribute_combinations") or []):
                    if ac.get("id")=="COLOR" or "color" in (ac.get("name","") or "").lower():
                        return _parse_color(ac.get("value_name"))
        except: pass
    return None

def clean_title(title, item_obj=None, H=None):
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
    color = None
    if item_obj is not None:
        color = get_variant_color(item_obj, H)
    if not color:
        color = _parse_color(t)
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

# Pre-tokenize todas las cuentas
TOKENS = {}
for a, rt in ACCS.items():
    if rt:
        t = tok(rt)
        if t: TOKENS[a] = t
print(f"Tokens disponibles para: {list(TOKENS.keys())}")

def find_in_all_accounts(oid, hint_acc=None):
    """Busca el oid como order/pack/shipment en todas las cuentas. Devuelve (acc, sid, items) o (None,None,None)."""
    order = [hint_acc] + [a for a in TOKENS.keys() if a != hint_acc] if hint_acc else list(TOKENS.keys())
    for a in order:
        if a not in TOKENS: continue
        H = {"Authorization": f"Bearer {TOKENS[a]}"}
        # 1) /orders
        o = requests.get(f"https://api.mercadolibre.com/orders/{oid}", headers=H, timeout=10).json()
        if isinstance(o, dict) and o.get("error") is None and not o.get("message","").startswith("Order do not exists"):
            sid = (o.get("shipping") or {}).get("id")
            items = o.get("order_items") or []
            if sid:
                return a, sid, items, H
        # 2) /shipments
        sh = requests.get(f"https://api.mercadolibre.com/shipments/{oid}", headers=H, timeout=10)
        if sh.status_code == 200:
            j = sh.json()
            if isinstance(j, dict) and j.get("status"):
                # buscar items via orders/search
                items=[]
                try:
                    qr = requests.get("https://api.mercadolibre.com/orders/search", headers=H, timeout=15,
                                      params={"shipping.id":oid}).json()
                    if qr.get("results"): items = qr["results"][0].get("order_items",[])
                except: pass
                return a, oid, items, H
        # 3) /packs
        pk = requests.get(f"https://api.mercadolibre.com/packs/{oid}", headers=H, timeout=10).json()
        if isinstance(pk, dict) and pk.get("orders"):
            for sub_o in pk["orders"]:
                sub_oid = sub_o.get("id")
                if not sub_oid: continue
                sub = requests.get(f"https://api.mercadolibre.com/orders/{sub_oid}", headers=H, timeout=10).json()
                sid = (sub.get("shipping") or {}).get("id")
                if sid:
                    return a, sid, sub.get("order_items",[]), H
    return None, None, None, None

writer = PdfWriter()
fail = []
ok = 0
for acc_hint, oid in targets:
    print(f"\n--- Buscando {oid} (hint: {acc_hint}) ---")
    acc, sid, items, H = find_in_all_accounts(oid, acc_hint)
    if not sid:
        print(f"  NO ENCONTRADO en ninguna cuenta")
        fail.append((acc_hint, oid, "no encontrado en ninguna cuenta")); continue
    print(f"  encontrado en cuenta={acc} sid={sid}")
    # Re-query order para obtener buyer (no lo trae find_in_all_accounts)
    buyer="?"
    try:
        oqr = requests.get("https://api.mercadolibre.com/orders/search", headers=H, timeout=10,
                           params={"shipping.id":sid}).json()
        if oqr.get("results"):
            buyer = ((oqr["results"][0].get("buyer") or {}).get("nickname")) or "?"
            if not items: items = oqr["results"][0].get("order_items",[])
    except: pass
    comp_lines=[]; has_used=False
    for it in items:
        io_obj = it.get("item") or {}
        title = clean_title(io_obj.get("title",""), io_obj, H)
        qty = it.get("quantity",1)
        cond = get_condition(io_obj, H)
        if cond == "used":
            has_used = True
            comp_lines.append(f"USADO {title} x{qty}")
        else:
            comp_lines.append(f"{title} x{qty}")
    if not comp_lines:
        comp_lines = [f"Order {oid}"]
    s = {"sid":sid,"account":acc,"buyer":buyer,"comp_lines":comp_lines,"has_used":has_used}
    print(f"  resolved -> sid={sid}  buyer={buyer}  used={has_used}  comp={comp_lines}")

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
