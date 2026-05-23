"""Wilbert (sin Grip) + Yiriam pendientes en 1 PDF, agrupado por producto.
FIX: si MELI devuelve un color que no está en el diccionario, se usa value_name tal cual.
"""
import os, io, time, requests
from datetime import datetime, timedelta, timezone
from collections import Counter
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from pdf2image import convert_from_bytes
from PIL import ImageOps

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCOUNTS = [
    ("Yiriam",  os.environ.get("MELI_REFRESH_TOKEN_YC_NEW")),
]
TZ = timezone(timedelta(hours=-6))
PAGE_W=4*72; PAGE_H=6*72
ALLOWED_SUBS = {"printed", "ready_to_print"}
# Exclusiones por cuenta: model exacto o substring del título
EXCLUDE_BY_ACC = {
    "Wilbert": {
        "models": {"Grip"},
        "title_contains": {"mandarin", "aqua"},
    },
    "Yiriam": {"models": set(), "title_contains": set()},
    "Asva":   {"models": set(), "title_contains": set()},
}
USED_LISTINGS = {"MLM2911205487", "MLM5295749840", "MLM2911241939"}


def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")


def _parse_color_map(text):
    """Mapea a un color estándar. Devuelve None si no matchea."""
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


def _normalize_value_name(text):
    """Si el value_name no matchea el diccionario, normalízalo (Title Case + clean)."""
    if not text: return None
    t = text.strip()
    # Quita prefijos comunes
    for prefix in ["Color ", "color "]:
        if t.startswith(prefix): t = t[len(prefix):]
    return t.title() if t else None


def get_variant_color(item_obj, H):
    """Intenta variation_attributes → variations endpoint → None.
    Si encuentra un value_name pero no matchea el map, lo devuelve tal cual."""
    # Path 1: variation_attributes (en order_items)
    attrs = item_obj.get("variation_attributes") or []
    for a in attrs:
        if a.get("id")=="COLOR" or "color" in (a.get("name","") or "").lower():
            vn = a.get("value_name") or ""
            c = _parse_color_map(vn)
            if c: return c
            n = _normalize_value_name(vn)
            if n: return n
    # Path 2: /items/{id}/variations/{vid}
    iid = item_obj.get("id"); vid = item_obj.get("variation_id")
    if iid and vid:
        try:
            r = requests.get(f"https://api.mercadolibre.com/items/{iid}/variations/{vid}",
                             headers=H, timeout=8)
            if r.status_code == 200:
                for ac in (r.json().get("attribute_combinations") or []):
                    if ac.get("id")=="COLOR" or "color" in (ac.get("name","") or "").lower():
                        vn = ac.get("value_name") or ""
                        c = _parse_color_map(vn)
                        if c: return c
                        n = _normalize_value_name(vn)
                        if n: return n
        except: pass
    return None


def get_model(title):
    t=(title or "").strip()
    tl_full = t.lower()
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
    # Listado JBL genérico en portugués: "Modelo Padrão" = modelo estándar
    if "modelo padrão" in tl_full or "modelo padrao" in tl_full or "padrão" in tl_full:
        return "JBL Impermeable"
    return t[:24]


def clean_title(item_obj, H):
    title = item_obj.get("title","")
    tl = title.lower()
    model = get_model(title)
    color = get_variant_color(item_obj, H)
    if not color:
        color = _parse_color_map(title)
    base = f"{model} {color}" if color else model
    # Sufijo (Reacond.) si el título lo indica
    if "reacondicionado" in tl or "reacond" in tl:
        base = f"{base} (Reacond.)"
    return base, model


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
        imgs = convert_from_bytes(pdf_bytes, dpi=72, first_page=page_idx+1, last_page=page_idx+1)
        if not imgs: return None
        img = imgs[0].convert("L")
        bw = img.point(lambda p: 0 if p < 245 else 255, mode="L")
        inv = ImageOps.invert(bw)
        bbox = inv.getbbox()
        if not bbox: return None
        x0, y0_top, x1, y1_top = bbox
        img_w, img_h = img.size
        m = 2
        return (max(0, x0-m), max(0, img_h - y1_top - m),
                min(img_w, x1-x0+2*m), min(img_h, y1_top-y0_top+2*m))
    except: return None


def render_header(s, header_h):
    has_used = bool(s.get("has_used"))
    n_prods = s.get("n_prods", len(s.get("comp_lines",[])))
    multi = n_prods > 1
    usado_strip = 14 if has_used else 0
    multi_strip = 14 if multi else 0
    total_h = header_h + usado_strip + multi_strip
    buf=io.BytesIO()
    c=canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    cx = PAGE_W/2.0
    # banda amarilla (datos + productos)
    c.setFillColor(Color(1, 0.96, 0.74))
    c.rect(0, PAGE_H-total_h, PAGE_W, header_h, fill=1, stroke=0)
    top = PAGE_H
    # banda roja USADO (si aplica) — arriba del todo
    if has_used:
        c.setFillColorRGB(0.85, 0.13, 0.13)
        c.rect(0, top-usado_strip, PAGE_W, usado_strip, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, top-11, "*** PRODUCTO USADO ***")
        top -= usado_strip
    # banda naranja MULTIPRODUCTO (si aplica)
    if multi:
        c.setFillColorRGB(0.90, 0.49, 0.13)
        c.rect(0, top-multi_strip, PAGE_W, multi_strip, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, top-11, f">>> ENVIO CON {n_prods} PRODUCTOS <<<")
        top -= multi_strip
    yellow_top = top
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(cx, yellow_top-11, f"[{s['account'].upper()}] {s['buyer'][:30]} | Ship:{s['sid']}")
    big = s["comp_lines"][:6]; n=len(big)
    # font/line-height adaptan al número de productos
    if n <= 2: fs, lh = 14, 16
    elif n <= 4: fs, lh = 12, 14
    else: fs, lh = 10, 12
    block_top=yellow_top-18; block_bot=PAGE_H-total_h+4
    block_h=block_top-block_bot; text_h=n*lh
    first_y = block_top - (block_h - text_h)/2.0 - fs*0.8
    c.setFont("Helvetica-Bold", fs)
    y=first_y
    for line in big:
        c.drawCentredString(cx, y, line[:34]); y-=lh
    c.showPage(); c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# === FASE 1: recolectar de ambas cuentas ===
NOW=datetime.now(timezone.utc)
START=NOW-timedelta(days=180)
all_shipments=[]
for acc_name, rt in ACCOUNTS:
    if not rt: print(f"--- {acc_name}: SIN TOKEN"); continue
    at = tok(rt)
    if not at: print(f"--- {acc_name}: token fail"); continue
    print(f"--- {acc_name} ---")
    H={"Authorization":f"Bearer {at}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
    uid=me.get("id")
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
    # AGRUPA todas las órdenes por shipment_id (un envío/pack puede tener varias órdenes)
    obs={}
    for o in orders:
        sid=(o.get("shipping") or {}).get("id")
        if sid: obs.setdefault(sid, []).append(o)
    matches=0; excluded_grip=0; no_color_warns=[]
    for sid, ord_list in obs.items():
        try:
            sh=requests.get(f"https://api.mercadolibre.com/shipments/{sid}",headers=H,timeout=10).json()
            st=sh.get("status"); substat=sh.get("substatus")
            if st!="ready_to_ship" or substat not in ALLOWED_SUBS: continue
            excl = EXCLUDE_BY_ACC.get(acc_name, {"models": set(), "title_contains": set()})
            # Junta TODOS los items de TODAS las órdenes del envío (packs)
            comp_lines=[]; has_used=False; skip_excl=False
            for ord_o in ord_list:
                for it in ord_o.get("order_items", []):
                    io_obj = it.get("item") or {}
                    title_cln, model = clean_title(io_obj, H)
                    raw_title = (io_obj.get("title") or "").lower()
                    resolved = title_cln.lower()
                    if model in excl["models"]:
                        skip_excl = True
                    if any(kw in raw_title or kw in resolved for kw in excl["title_contains"]):
                        skip_excl = True
                    qty = it.get("quantity",1)
                    iid = io_obj.get("id") or ""
                    cond = get_condition(io_obj, H)
                    # Formato reducido en español: "{cant} {Modelo} {Color}"
                    if iid in USED_LISTINGS or cond == "used":
                        has_used=True
                        comp_lines.append(f"USADO {qty} {title_cln}")
                    else:
                        comp_lines.append(f"{qty} {title_cln}")
                    if title_cln == model:
                        no_color_warns.append((sid, ord_o.get("id"), io_obj.get("id"), io_obj.get("variation_id"), io_obj.get("title","")[:60]))
            if skip_excl:
                excluded_grip += 1; continue
            buyer=(ord_list[0].get("buyer") or {}).get("nickname","?")
            n_prods = len(comp_lines)
            all_shipments.append({"sid":sid,"account":acc_name,"token":at,
                                  "comp_lines":comp_lines,"buyer":buyer,
                                  "has_used":has_used,"substatus":substat,
                                  "n_prods":n_prods,
                                  "tracking":sh.get("tracking_number","")})
            matches+=1
            time.sleep(0.04)
        except Exception as e:
            print(f"  err {sid}: {str(e)[:80]}")
    print(f"  matches: {matches} (excluidos por filtro cuenta: {excluded_grip})")
    if no_color_warns:
        print(f"  *** AVISO: {len(no_color_warns)} items sin color detectado:")
        for w in no_color_warns[:10]:
            print(f"     sid={w[0]} order={w[1]} item={w[2]} var={w[3]} title={w[4]!r}")

print(f"\nTotal shipments seleccionados: {len(all_shipments)}")
multi = [s for s in all_shipments if s.get("n_prods",1) > 1]
print(f"Envíos con MÚLTIPLES productos: {len(multi)}")
for s in multi:
    print(f"   sid={s['sid']} [{s['account']}] ({s['n_prods']} prods): {' + '.join(s['comp_lines'])}")
# Sort por producto (USADO primero, luego multiproducto agrupado, luego por producto)
all_shipments.sort(key=lambda s: (0 if s["has_used"] else 1, "/".join(s["comp_lines"]), s["sid"]))


# === FASE 2: PDF ===
print("\n=== Generando PDF ===")
writer=PdfWriter()
fail=[]
for s in all_shipments:
    H={"Authorization":f"Bearer {s['token']}"}
    try:
        r=requests.get("https://api.mercadolibre.com/shipment_labels",
                      headers=H, params={"shipment_ids":s["sid"],"response_type":"pdf"},
                      timeout=30)
        if r.status_code!=200 or not r.headers.get("content-type","").lower().startswith("application/pdf"):
            fail.append(s["sid"]); continue
        raw=r.content
        lbl_pdf=PdfReader(io.BytesIO(raw))
        for pidx,label_page in enumerate(lbl_pdf.pages):
            box = label_page.cropbox if label_page.cropbox else label_page.mediabox
            lbl_x0=float(box.left); lbl_y0=float(box.bottom)
            lbl_w=float(box.width); lbl_h=float(box.height)
            cb = detect_content_bbox(raw, pidx)
            if cb:
                cx0,cy0,cw,ch = cb
                lbl_x0=float(box.left)+float(cx0)
                lbl_y0=float(box.bottom)+float(cy0)
                lbl_w=float(cw); lbl_h=float(ch)
            n_lines=min(len(s["comp_lines"]),6)
            header_h = 22 + n_lines*15
            label_area_h = PAGE_H - header_h
            new_page = PageObject.create_blank_page(width=PAGE_W, height=PAGE_H)
            sx = PAGE_W/lbl_w; sy = label_area_h/lbl_h
            op = (Transformation().translate(-lbl_x0,-lbl_y0).scale(sx,sy))
            new_page.merge_transformed_page(label_page, op)
            new_page.merge_page(render_header(s, header_h))
            writer.add_page(new_page)
    except Exception as e:
        fail.append(s["sid"])
    time.sleep(0.08)

with open("ETIQUETAS_YIRIAM_TODAS.pdf","wb") as f: writer.write(f)
print(f"\n✅ PDF: ETIQUETAS_YIRIAM_TODAS.pdf ({len(writer.pages)} págs) | Fallidas: {len(fail)}")

print("\n=== Top productos ===")
prods=Counter("/".join(s["comp_lines"]) for s in all_shipments)
for p,n in sorted(prods.items(), key=lambda x:-x[1])[:25]: print(f"  {n:3} {p}")
