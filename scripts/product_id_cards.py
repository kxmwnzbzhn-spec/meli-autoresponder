"""Tarjetas identificadoras 4x6 in para cada producto único que vendemos.
Para cada (modelo + color) saca: TEXTO GRANDE + imagen del listado MELI.
Recorre TODAS las cuentas, deduplica por (modelo, color).
"""
import os, io, time, requests
from collections import defaultdict
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

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


def parse_model(title):
    t=(title or "").strip()
    for w in ["Bocina ","bocina ","Parlante ","parlante ","Altavoz ","altavoz ","Speaker ","speaker ",
              "JBL ","jbl ","Jbl ","Sony ","SONY ","Bose ","BOSE "]:
        t=t.replace(w,"")
    tl=t.lower()
    if "go 4" in tl or "go4" in tl: return "Go 4"
    if "go 3" in tl or "go3" in tl: return "Go 3"
    if "clip 5" in tl or "clip5" in tl: return "Clip 5"
    if "charge 6" in tl or "charge6" in tl: return "Charge 6"
    if "flip 7" in tl or "flip7" in tl: return "Flip 7"
    if "grip" in tl: return "Grip"
    if "xb100" in tl: return "Sony XB100"
    if "soundlink" in tl: return "Bose SoundLink"
    if any(w in tl for w in ["perfume","parfum","edp","edt","eau de","fragancia","lattafa","armaf","billie eilish"]):
        # Para perfumes, modelo = primeras 28 chars del título limpio
        return f"Perfume: {t[:28]}"
    return t[:30]


# === FASE 1: Recolecta listings activos de cada cuenta ===
print("=== Recolectando listings activos ===")
seen = {}  # (model, color) -> {"model","color","listing_id","variation_id","picture_url","title","account"}
for acc, rt in ACCS.items():
    if not rt: print(f"--- {acc}: SIN TOKEN"); continue
    at = tok(rt)
    if not at: print(f"--- {acc}: token fail"); continue
    print(f"--- {acc} ---")
    H={"Authorization":f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
    uid = me.get("id")
    if not uid: continue

    # Lista IDs de items activos
    ids=[]; offset=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search",
                       headers=H, params={"status":"active","limit":100,"offset":offset}, timeout=20).json()
        chunk = r.get("results",[])
        if not chunk: break
        ids.extend(chunk); offset+=len(chunk)
        if offset>=r.get("paging",{}).get("total",0): break
    print(f"  active items: {len(ids)}")

    # Fetch detalles en batches de 20 vía multiget
    for batch_start in range(0, len(ids), 20):
        batch = ids[batch_start:batch_start+20]
        try:
            mg = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(batch)}",
                              headers=H, timeout=20).json()
        except Exception as e:
            print(f"  err multiget: {e}"); continue
        for entry in mg:
            if entry.get("code") != 200: continue
            it = entry.get("body") or {}
            iid = it.get("id")
            title = it.get("title","")
            model = parse_model(title)
            variations = it.get("variations") or []
            thumb_default = it.get("thumbnail") or it.get("secure_thumbnail") or ""
            pictures = it.get("pictures") or []
            if not variations:
                color = _parse_color(title) or ""
                key=(model,color)
                if key in seen: continue
                seen[key]={"model":model,"color":color,"listing_id":iid,"variation_id":"",
                           "picture_url":(pictures[0].get("secure_url") if pictures else thumb_default),
                           "title":title,"account":acc}
            else:
                # picture_id_to_url
                pic_map = {p["id"]:p.get("secure_url") for p in pictures}
                for v in variations:
                    color=None
                    for ac in (v.get("attribute_combinations") or []):
                        if ac.get("id")=="COLOR" or "color" in (ac.get("name","") or "").lower():
                            color = _parse_color(ac.get("value_name") or "") or (ac.get("value_name") or "")
                            break
                    color = color or ""
                    key=(model,color)
                    if key in seen: continue
                    pids = v.get("picture_ids") or []
                    purl = ""
                    for pid in pids:
                        if pid in pic_map: purl = pic_map[pid]; break
                    if not purl and pictures: purl = pictures[0].get("secure_url")
                    seen[key]={"model":model,"color":color,"listing_id":iid,"variation_id":v.get("id",""),
                               "picture_url":purl,"title":title,"account":acc}
        time.sleep(0.1)

print(f"\n=== Productos únicos: {len(seen)} ===")

# === FASE 2: Render PDF ===
print("=== Generando PDF tarjetas ===")
writer = PdfWriter()
items_sorted = sorted(seen.values(), key=lambda x: (x["model"], x["color"]))

def fit_font(c, text, max_width, base_size, font="Helvetica-Bold", min_size=24):
    """Devuelve un size que hace que text quepa en max_width."""
    sz = base_size
    while sz > min_size:
        if c.stringWidth(text, font, sz) <= max_width: return sz
        sz -= 2
    return min_size

for p in items_sorted:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    cx = PAGE_W/2.0
    MARGIN = 10
    max_w = PAGE_W - 2*MARGIN
    c.setFillColorRGB(0,0,0)

    model = p["model"]
    color = (p["color"] or "").upper()
    # Si el modelo empieza con "Perfume:" lo tratamos especial (texto más chico, sin color)
    is_perfume = model.lower().startswith("perfume") or any(w in model.lower() for w in
                                                            ["edp","edt","gucci","marc jacobs","dior","creed","byredo",
                                                             "le labo","jo milano","initio","dolce","gabbana","santal",
                                                             "billie eilish","armaf","lattafa","marshmallow","my way",
                                                             "flora","daisy","sauvage","silver mountain"])

    if is_perfume:
        # Perfume: nombre limpio sin prefijo
        name = model.replace("Perfume: ","").replace("Perfume:","").strip()
        # 1-3 líneas wrapped
        words = name.split()
        lines=[]; cur=""
        for w in words:
            test = (cur+" "+w).strip()
            if c.stringWidth(test, "Helvetica-Bold", 32) <= max_w:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        lines = lines[:4]
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(cx, PAGE_H-20, "PERFUME")
        # Centrar verticalmente
        line_h = 38
        block_h = len(lines)*line_h
        y = (PAGE_H + block_h)/2 - 8
        for ln in lines:
            sz = fit_font(c, ln, max_w, 32, min_size=18)
            c.setFont("Helvetica-Bold", sz)
            c.drawCentredString(cx, y, ln)
            y -= line_h
    else:
        # Bocina (modelo grande + color enorme)
        # Linea modelo arriba (más grande)
        sz_model = fit_font(c, model, max_w, 64, min_size=32)
        c.setFont("Helvetica-Bold", sz_model)
        c.drawCentredString(cx, PAGE_H/2 + 50, model)
        # Color ENORME debajo
        if color:
            sz_col = fit_font(c, color, max_w, 90, min_size=40)
            c.setFont("Helvetica-Bold", sz_col)
            c.drawCentredString(cx, PAGE_H/2 - 50, color)

    # Footer (chico) - cuenta + listing_id para referencia
    c.setFont("Helvetica", 7)
    foot = f"{p['account']} · {p['listing_id']}"
    if p.get("variation_id"): foot += f" · var {p['variation_id']}"
    c.drawCentredString(cx, 14, foot)

    c.showPage(); c.save()
    buf.seek(0)
    writer.add_page(PdfReader(buf).pages[0])

with open("ETIQUETAS_PRODUCTOS_IDENTIFICACION.pdf","wb") as f: writer.write(f)
print(f"✅ PDF: ETIQUETAS_PRODUCTOS_IDENTIFICACION.pdf ({len(writer.pages)} págs)")

# Imprime resumen
print("\n=== Productos en el PDF ===")
for p in items_sorted:
    img = "✓" if p.get("picture_url") else "✗"
    print(f"  {img}  {p['model']:25} {p['color']:12} listing={p['listing_id']} [{p['account']}]")
