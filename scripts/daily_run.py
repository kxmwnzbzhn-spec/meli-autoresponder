"""DAILY RUN — Sistema autónomo de etiquetas.

Para cada cuenta (Yiriam, Asva):
  1. Renueva token y valida que el UID coincida con el esperado (anti-error: evita usar token cruzado).
  2. Saca shipments pendientes (ready_to_ship + printed/ready_to_print).
  3. Genera PDF 4x6 con formato compacto en español + packs multi-producto.
  4. Compara conteo con el día anterior (stats.json en Drive); alerta si la caída > 70% o subida > 5x.
  5. Sube PDF al folder de Drive con nombre fechado.
  6. Notifica Telegram con resumen y links.

NUNCA sube un PDF vacío. Si falla una cuenta sigue con la otra y reporta el error.
"""
import os, io, time, json, sys, traceback, re, requests
from datetime import datetime, timedelta, timezone
from collections import Counter
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from pdf2image import convert_from_bytes
from PIL import ImageOps

APP_ID = os.environ.get("MELI_APP_ID", "2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]
APP_ID_NEW = os.environ.get("MELI_APP_ID_NEW", "5211907102822632")
APP_SECRET_NEW = os.environ.get("MELI_APP_SECRET_NEW", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL")
LEDGER_NAME = "printed_shipments_ALL.json"
TZ = timezone(timedelta(hours=-6))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")
PAGE_W = 4*72; PAGE_H = 6*72

# Cuentas con metadata anti-error (uid y nickname esperados — si no coinciden, abortar esa cuenta)
ACCOUNTS = [
    {"name":"Claribel","rt_env":"MELI_REFRESH_TOKEN_CLARIBEL","expected_uid":3348766821,"expected_nick":"CX20260420180750",
     "exclude_models":set(), "exclude_titles":set()},
    {"name":"Asva",    "rt_env":"MELI_REFRESH_TOKEN_ASVA",    "expected_uid":1668713481,"expected_nick":"ASVAELECTRONICS",
     "exclude_models":set(), "exclude_titles":set()},
    {"name":"RocioAngel","rt_env":"MELI_REFRESH_TOKEN_ROCIOANGEL","expected_uid":3478435727,"expected_nick":"RF20260617003604",
     "exclude_models":set(), "exclude_titles":set()},
    {"name":"Edilberto","rt_env":"MELI_REFRESH_TOKEN_EDILBERTO","expected_uid":3616975257,"expected_nick":"ER20260815153348465",
     "app_pair":"new", "exclude_models":set(), "exclude_titles":set()},
    {"name":"LuisEd","rt_env":"MELI_REFRESH_TOKEN_LUISED","expected_uid":3584846108,"expected_nick":"LG20260801171031460",
     "app_pair":"new", "exclude_models":set(), "exclude_titles":set()},
    {"name":"JorgeLuis","rt_env":"MELI_REFRESH_TOKEN_JORGE_LUIS","expected_uid":3640697853,"expected_nick":None,
     "app_pair":"new", "exclude_models":set(), "exclude_titles":set()},
]
EXCLUDED_SUBS = {"picked_up"}
# Solo estos substatuses son "listas para acción del vendedor":
# - ready_to_print / printing_error: pendientes de imprimir
# - printed: impresas listas para entregar en agencia
# - invoice_pending: esperando factura pero contable
INCLUDED_SUBS = {"ready_to_print", "printing_error", "printed", "invoice_pending"}
TOMORROW = (datetime.now(TZ) + timedelta(days=1)).strftime("%Y-%m-%d")

def extract_limit_date_str(sh):
    """Devuelve YYYY-MM-DD CDMX del handling_limit del shipment, o None."""
    dh = sh.get("date_handling") or {}
    ehl = dh.get("estimated_handling_limit") or {}
    dstr = ehl.get("date") or ""
    if not dstr:
        so = sh.get("shipping_option") or {}
        ehl2 = so.get("estimated_handling_limit") or {}
        dstr = ehl2.get("date") or ""
    if not dstr:
        sh_hist = sh.get("status_history") or {}
        dstr = sh_hist.get("date_handling") or ""
    if not dstr: return None
    try:
        s = re.sub(r"\.\d+", "", dstr)
        dt = datetime.fromisoformat(s)
        return dt.astimezone(TZ).strftime("%Y-%m-%d")
    except Exception:
        return None


# ============ HELPERS DE COLOR/MODELO/CONDICIÓN ============

def _parse_color_map(text):
    if not text: return None
    tl = " "+text.lower()+" "
    cm = [("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
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
    t = text.strip()
    for p in ["Color ","color "]:
        if t.startswith(p): t = t[len(p):]
    return t.title() if t else None

def get_variant_color(item_obj, H):
    for a in (item_obj.get("variation_attributes") or []):
        if a.get("id")=="COLOR" or "color" in (a.get("name","") or "").lower():
            vn = a.get("value_name") or ""
            return _parse_color_map(vn) or _norm(vn)
    iid = item_obj.get("id"); vid = item_obj.get("variation_id")
    if iid and vid:
        try:
            r = requests.get(f"https://api.mercadolibre.com/items/{iid}/variations/{vid}", headers=H, timeout=8)
            if r.status_code == 200:
                for ac in (r.json().get("attribute_combinations") or []):
                    if ac.get("id")=="COLOR" or "color" in (ac.get("name","") or "").lower():
                        vn = ac.get("value_name") or ""
                        return _parse_color_map(vn) or _norm(vn)
        except: pass
    return None

def get_model(title):
    t = (title or "").strip(); tl_full = t.lower()
    for w in ["Bocina ","bocina ","Parlante ","parlante ","Altavoz ","altavoz ","Speaker ","speaker ",
              "JBL ","jbl ","Jbl ","Sony ","SONY ","Bose ","BOSE "]:
        t = t.replace(w, "")
    tl = t.lower()
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

def _marshall_model(item_obj, H):
    """Obtiene el modelo Marshall real; evita títulos genéricos o truncados."""
    iid = item_obj.get("id")
    candidates = [item_obj.get("title", "")]
    if iid:
        try:
            r = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=8)
            if r.status_code == 200:
                detail = r.json() or {}
                candidates.append(detail.get("title", ""))
                for attr in detail.get("attributes") or []:
                    if attr.get("id") in {"MODEL", "LINE", "ALPHANUMERIC_MODEL"}:
                        candidates.append(attr.get("value_name", ""))
        except Exception:
            pass
    joined = " ".join(x for x in candidates if x).lower()
    if "willen" in joined:
        return "Marshall Willen II" if "willen ii" in joined or "willen 2" in joined else "Marshall Willen"
    if "emberton" in joined:
        if "emberton iii" in joined or "emberton 3" in joined:
            return "Marshall Emberton III"
        if "emberton ii" in joined or "emberton 2" in joined:
            return "Marshall Emberton II"
        return "Marshall Emberton"
    if "middleton" in joined: return "Marshall Middleton"
    if "stockwell" in joined: return "Marshall Stockwell"
    if "kilburn" in joined: return "Marshall Kilburn"
    return None

def clean_title(item_obj, H):
    title = item_obj.get("title","")
    tl = title.lower()
    model = _marshall_model(item_obj, H) if ("marshall" in tl or "marsh" in tl) else None
    model = model or get_model(title)
    color = get_variant_color(item_obj, H) or _parse_color_map(title)
    base = f"{model} {color}" if color else model
    if "reacondicionado" in tl or "reacond" in tl: base = f"{base} (Reacond.)"
    return base, model

_CC = {}
def get_condition(item_obj, H):
    c = item_obj.get("condition")
    if c: return c
    iid = item_obj.get("id")
    if not iid: return None
    if iid in _CC: return _CC[iid]
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=8,
                         params={"attributes":"condition"})
        if r.status_code == 200:
            c = (r.json() or {}).get("condition")
            _CC[iid] = c; return c
    except: pass
    _CC[iid] = None; return None


# ============ PDF RENDERING ============

def detect_bbox(pdf_bytes, pi=0):
    try:
        imgs = convert_from_bytes(pdf_bytes, dpi=72, first_page=pi+1, last_page=pi+1)
        if not imgs: return None
        img = imgs[0].convert("L")
        bw = img.point(lambda p: 0 if p < 245 else 255, mode="L")
        inv = ImageOps.invert(bw); bb = inv.getbbox()
        if not bb: return None
        x0, y0t, x1, y1t = bb; iw, ih = img.size
        m = 2
        return (max(0, x0-m), max(0, ih-y1t-m), min(iw, x1-x0+2*m), min(ih, y1t-y0t+2*m))
    except: return None

def render_header(s, header_h):
    has_used = bool(s.get("has_used"))
    n_prods = s.get("n_prods", len(s.get("comp_lines", [])))
    multi = n_prods > 1
    us = 14 if has_used else 0
    mu = 14 if multi else 0
    total_h = header_h + us + mu
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    cx = PAGE_W/2.0
    c.setFillColor(Color(1, 0.96, 0.74))
    c.rect(0, PAGE_H-total_h, PAGE_W, header_h, fill=1, stroke=0)
    top = PAGE_H
    if has_used:
        c.setFillColorRGB(0.85, 0.13, 0.13); c.rect(0, top-us, PAGE_W, us, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, top-11, "*** PRODUCTO USADO ***"); top -= us
    if multi:
        c.setFillColorRGB(0.90, 0.49, 0.13); c.rect(0, top-mu, PAGE_W, mu, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, top-11, f">>> ENVIO CON {n_prods} PRODUCTOS <<<"); top -= mu
    yt = top
    c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(cx, yt-11, f"[{s['account'].upper()}] {s['buyer'][:30]} | Ship:{s['sid']}")
    big = s["comp_lines"][:6]; n = len(big)
    fs, lh = (14, 16) if n <= 2 else (12, 14) if n <= 4 else (10, 12)
    bt = yt-18; bb = PAGE_H-total_h+4
    bh = bt-bb; th = n*lh
    fy = bt - (bh - th)/2.0 - fs*0.8
    c.setFont("Helvetica-Bold", fs)
    y = fy
    for line in big:
        c.drawCentredString(cx, y, line[:34]); y -= lh
    c.showPage(); c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# ============ TOKEN + ACCOUNT VALIDATION ============

def renew_token(rt, account):
    use_new = account.get("app_pair") == "new"
    app_id = APP_ID_NEW if use_new else APP_ID
    app_secret = APP_SECRET_NEW if use_new else APP_SECRET
    if not app_secret:
        return {"error":"missing_app_secret","message":f"Falta secreto de app para {account['name']}"}
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":app_id,"client_secret":app_secret,"refresh_token":rt}, timeout=15)
    return r.json()

def validate_account(account):
    """Renueva token y verifica uid+nick. Devuelve (access_token, error_msg)."""
    rt = os.environ.get(account["rt_env"])
    if not rt:
        return None, f"No hay token (env {account['rt_env']} vacío)"
    j = renew_token(rt, account)
    at = j.get("access_token")
    if not at:
        return None, f"token fail: {j.get('error')} {j.get('message','')[:120]}"
    me = requests.get("https://api.mercadolibre.com/users/me",
                      headers={"Authorization":f"Bearer {at}"}, timeout=15).json()
    if me.get("id") != account["expected_uid"]:
        return None, f"UID NO COINCIDE: esperado={account['expected_uid']} recibido={me.get('id')} (token cruzado?)"
    if account.get("expected_nick") and me.get("nickname") != account["expected_nick"]:
        return None, f"Nickname NO COINCIDE: esperado={account['expected_nick']} recibido={me.get('nickname')}"
    return at, None


# ============ COLLECT SHIPMENTS + PDF ============

def collect_shipments(at, account):
    H = {"Authorization":f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me["id"]
    NOW = datetime.now(timezone.utc); START = NOW - timedelta(days=180)
    orders=[]; off=0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search", headers=H, timeout=20,
            params={"seller":uid,"order.status":"paid",
                    "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":off}).json()
        res = r.get("results", [])
        if not res: break
        orders.extend(res); off += len(res)
        if off >= r.get("paging",{}).get("total", 0): break
    obs = {}
    for o in orders:
        sid = (o.get("shipping") or {}).get("id")
        if sid: obs.setdefault(sid, []).append(o)
    ships=[]
    excl_models = account["exclude_models"]; excl_titles = account["exclude_titles"]
    for sid, ord_list in obs.items():
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10).json()
            st = sh.get("status"); sub = sh.get("substatus")
            # Filtro estricto: solo shipments accionables por el vendedor
            if st != "ready_to_ship": continue
            if sub not in INCLUDED_SUBS: continue  # skip picked_up y otros no accionables
            # Filtro fecha: incluye HOY + DEMORADAS + MAÑANA (todo lo que puede entregarse hoy o mañana)
            ld = extract_limit_date_str(sh)
            if ld is not None and ld > TOMORROW: continue  # descarta si límite pasa mañana
            comp=[]; used=False; skip=False
            for ord_o in ord_list:
                for it in ord_o.get("order_items", []):
                    io_obj = it.get("item") or {}
                    tcln, model = clean_title(io_obj, H)
                    if model in excl_models: skip = True
                    rt_ = (io_obj.get("title") or "").lower(); rcln = tcln.lower()
                    if any(kw in rt_ or kw in rcln for kw in excl_titles): skip = True
                    qty = it.get("quantity", 1)
                    cond = get_condition(io_obj, H)
                    if cond == "used":
                        used = True; comp.append(f"USADO {qty} {tcln}")
                    else:
                        comp.append(f"{qty} {tcln}")
            if skip: continue
            if not comp: continue
            buyer = (ord_list[0].get("buyer") or {}).get("nickname", "?")
            ships.append({"sid":sid,"account":account["name"],"buyer":buyer,
                          "comp_lines":comp,"has_used":used,"n_prods":len(comp),
                          "at": at})
            time.sleep(0.04)
        except Exception as e:
            print(f"  err shipment {sid}: {str(e)[:80]}")
    ships.sort(key=lambda s: (0 if s["has_used"] else 1, "/".join(s["comp_lines"]), s["sid"]))
    return ships

def build_pdf(ships, out_path):
    """Cada shipment trae su propio access_token en s['at'] (multi-cuenta)."""
    writer = PdfWriter(); fail=[]
    for s in ships:
        H = {"Authorization":f"Bearer {s['at']}"}
        try:
            r = requests.get("https://api.mercadolibre.com/shipment_labels", headers=H,
                params={"shipment_ids":s["sid"], "response_type":"pdf"}, timeout=30)
            if r.status_code != 200 or not r.headers.get("content-type","").lower().startswith("application/pdf"):
                fail.append(s["sid"]); continue
            raw = r.content; lp = PdfReader(io.BytesIO(raw))
            # Mercado Libre puede adjuntar una segunda página de picking list.\n            # La primera página es la etiqueta logística; nunca incluir las demás.\n            if not lp.pages:\n                fail.append(s["sid"]); continue\n            for pi, page in enumerate([lp.pages[0]]):
                box = page.cropbox if page.cropbox else page.mediabox
                lx0=float(box.left); ly0=float(box.bottom); lw=float(box.width); lh=float(box.height)
                bb = detect_bbox(raw, pi)
                if bb:
                    cx0,cy0,cw,ch = bb
                    lx0=float(box.left)+float(cx0); ly0=float(box.bottom)+float(cy0); lw=float(cw); lh=float(ch)
                nl = min(len(s["comp_lines"]), 6); header_h = 22 + nl*15
                la = PAGE_H - header_h
                np_ = PageObject.create_blank_page(width=PAGE_W, height=PAGE_H)
                sx = PAGE_W/lw; sy = la/lh
                op = Transformation().translate(-lx0,-ly0).scale(sx,sy)
                np_.merge_transformed_page(page, op)
                np_.merge_page(render_header(s, header_h))
                writer.add_page(np_)
        except Exception as e:
            fail.append(s["sid"])
        time.sleep(0.08)
    with open(out_path, "wb") as f: writer.write(f)
    return len(writer.pages), fail


# ============ GOOGLE DRIVE ============

def drive_service():
    """Prioriza OAuth user (consume cuota del usuario). SA solo como fallback
    (en Gmail personal no tiene cuota, así que upload falla con storageQuotaExceeded)."""
    from googleapiclient.discovery import build
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    errors = []
    # 1) OAuth user delegation
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    rt = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")
    if cid and csec and rt:
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            creds = Credentials(token=None, refresh_token=rt,
                                token_uri="https://oauth2.googleapis.com/token",
                                client_id=cid, client_secret=csec, scopes=SCOPES)
            creds.refresh(Request())
            svc = build("drive", "v3", credentials=creds, cache_discovery=False)
            svc.files().get(fileId=DRIVE_FOLDER_ID, fields="id,name",
                            supportsAllDrives=True).execute()
            print("[drive] auth=OAuth user")
            return svc
        except Exception as e:
            errors.append(f"OAuth: {str(e)[:200]}")
    # 2) Service Account fallback (solo útil en Shared Drives)
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            from google.oauth2 import service_account
            info = json.loads(sa_json)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            svc = build("drive", "v3", credentials=creds, cache_discovery=False)
            svc.files().get(fileId=DRIVE_FOLDER_ID, fields="id,name",
                            supportsAllDrives=True).execute()
            print(f"[drive] auth=SA (fallback) email={info.get('client_email')}")
            return svc
        except Exception as e:
            errors.append(f"SA: {str(e)[:200]}")
    raise RuntimeError(
        "No se pudo autenticar contra Drive. Causas posibles:\n  " +
        "\n  ".join(errors) +
        f"\nRenovar GOOGLE_OAUTH_REFRESH_TOKEN.")

def drive_find_or_get_stats(svc):
    """Lee stats.json del folder o devuelve dict vacío."""
    res = svc.files().list(
        q=f"name='stats.json' and '{DRIVE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id,name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res.get("files", [])
    if not files: return {}, None
    fid = files[0]["id"]
    try:
        content = svc.files().get_media(fileId=fid, supportsAllDrives=True).execute()
        return json.loads(content.decode("utf-8") if isinstance(content, bytes) else content), fid
    except: return {}, fid

def drive_save_stats(svc, stats, file_id=None):
    from googleapiclient.http import MediaInMemoryUpload
    body = json.dumps(stats, indent=2, ensure_ascii=False).encode("utf-8")
    media = MediaInMemoryUpload(body, mimetype="application/json")
    if file_id:
        svc.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
    else:
        svc.files().create(body={"name":"stats.json","parents":[DRIVE_FOLDER_ID]},
                           media_body=media, supportsAllDrives=True).execute()

def drive_load_json(svc, name):
    """Carga un JSON de control desde la carpeta raíz de Drive."""
    safe = name.replace("'", "\\'")
    res = svc.files().list(
        q=f"name='{safe}' and '{DRIVE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id,name)", pageSize=10,
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res.get("files", [])
    if not files:
        return {}, None
    fid = files[0]["id"]
    try:
        content = svc.files().get_media(fileId=fid, supportsAllDrives=True).execute()
        return json.loads(content.decode("utf-8") if isinstance(content, bytes) else content), fid
    except Exception as e:
        raise RuntimeError(f"No se pudo leer {name}: {e}")


def drive_save_json(svc, name, data, file_id=None):
    """Guarda de forma atómica el registro de guías ya emitidas."""
    from googleapiclient.http import MediaInMemoryUpload
    body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    media = MediaInMemoryUpload(body, mimetype="application/json")
    if file_id:
        svc.files().update(fileId=file_id, media_body=media,
                           supportsAllDrives=True).execute()
        return file_id
    created = svc.files().create(
        body={"name":name, "parents":[DRIVE_FOLDER_ID]},
        media_body=media, fields="id", supportsAllDrives=True).execute()
    return created["id"]


def drive_load_or_bootstrap_emitted(svc, output_prefix):
    """Carga el historial de shipment IDs.

    En la primera ejecución reconstruye el historial leyendo los encabezados Ship:
    de los PDFs de días anteriores. Nunca toma PDFs del día actual, para poder
    reemplazar de forma segura un archivo incorrecto con FORCE_REGEN=1.
    """
    data, fid = drive_load_json(svc, LEDGER_NAME)
    if fid:
        data.setdefault("shipments", {})
        return data, fid, 0

    # Migra los dos registros anteriores al registro global antes del primer
    # consolidado unificado. Así ninguna cuenta pierde su historial.
    shipments = {}
    for legacy_name in (
        "printed_shipments_ETIQUETAS.json",
        "printed_shipments_ETIQUETAS_EDILBERTO_LUISED.json",
    ):
        legacy, _ = drive_load_json(svc, legacy_name)
        shipments.update((legacy or {}).get("shipments", {}))
    q = (f"mimeType='application/vnd.google-apps.folder' and "
         f"'{DRIVE_FOLDER_ID}' in parents and trashed=false")
    res = svc.files().list(
        q=q, fields="files(id,name)", pageSize=1000,
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    for folder in res.get("files", []):
        day = folder.get("name", "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) or day >= TODAY:
            continue
        for prefix in ("ETIQUETAS", "ETIQUETAS_EDILBERTO_LUISED", "ETIQUETAS_UNIFICADAS"):
            pdf_name = f"{prefix}_{day}.pdf"
            safe_pdf = pdf_name.replace("'", "\\'")
            found = svc.files().list(
                q=f"name='{safe_pdf}' and '{folder['id']}' in parents and trashed=false",
                fields="files(id,name)", pageSize=10,
                supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            for pdf_file in found.get("files", [])[:1]:
                try:
                    raw = svc.files().get_media(
                        fileId=pdf_file["id"], supportsAllDrives=True).execute()
                    reader = PdfReader(io.BytesIO(raw))
                    for page in reader.pages:
                        text_ = page.extract_text() or ""
                        match = re.search(r"Ship:\s*(\d+)", text_)
                        if match:
                            shipments[match.group(1)] = {
                                "date": day, "source_file_id": pdf_file["id"]
                            }
                except Exception as e:
                    print(f"  bootstrap omitió {pdf_name}: {type(e).__name__}: {str(e)[:100]}")

    data = {"shipments": shipments, "bootstrapped_at": TODAY,
            "output_prefix": "ALL"}
    fid = drive_save_json(svc, LEDGER_NAME, data)
    print(f"[dedupe] historial inicial: {len(shipments)} guías previas")
    return data, fid, len(shipments)


def drive_find_or_create_day_folder(svc, parent_id, day_name):
    """Devuelve el folder_id de la subcarpeta '<day_name>' dentro de parent_id.
    Si no existe, la crea. Anti-empleados: cada día tiene su propia carpeta."""
    safe = day_name.replace("'", "\\'")
    q = (f"name='{safe}' and mimeType='application/vnd.google-apps.folder' "
         f"and '{parent_id}' in parents and trashed=false")
    res = svc.files().list(q=q, fields="files(id,name)",
                           supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res.get("files", [])
    if files:
        print(f"[drive] subcarpeta {day_name} ya existe: {files[0]['id']}")
        return files[0]["id"]
    body = {"name": day_name, "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id]}
    f = svc.files().create(body=body, fields="id,name,webViewLink",
                           supportsAllDrives=True).execute()
    print(f"[drive] subcarpeta {day_name} creada: {f['id']}")
    return f["id"]

def drive_upload_pdf(svc, local_path, drive_name, parent_id, max_retries=4):
    """Upload con resumable + retry exponencial (SSL EOF y similares).
    parent_id: la carpeta destino (puede ser la subcarpeta del día)."""
    from googleapiclient.http import MediaFileUpload
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            media = MediaFileUpload(local_path, mimetype="application/pdf",
                                    resumable=True, chunksize=1024*1024)
            req = svc.files().create(
                body={"name": drive_name, "parents":[parent_id]},
                media_body=media, supportsAllDrives=True,
                fields="id,name,webViewLink",
            )
            resp = None
            while resp is None:
                _, resp = req.next_chunk(num_retries=3)
            return resp
        except Exception as e:
            last_err = e
            print(f"  upload attempt {attempt} failed: {type(e).__name__}: {str(e)[:200]}", flush=True)
            time.sleep(2 ** attempt)
    raise last_err


# ============ TELEGRAM ============

def tg_send(text):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id":TG_CHAT, "text":text, "parse_mode":"HTML", "disable_web_page_preview":"true"},
            timeout=10)
    except: pass


# ============ MAIN ============

def already_done_today(svc):
    """Idempotencia: si la subcarpeta del día ya tiene ETIQUETAS_<TODAY>.pdf, no rehacer."""
    output_prefix = os.environ.get("OUTPUT_PREFIX", "ETIQUETAS")
    safe = TODAY.replace("'", "\\'")
    q = (f"name='{safe}' and mimeType='application/vnd.google-apps.folder' "
         f"and '{DRIVE_FOLDER_ID}' in parents and trashed=false")
    res = svc.files().list(q=q, fields="files(id,name)",
                           supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    folders = res.get("files", [])
    if not folders: return None
    day_id = folders[0]["id"]
    pdf_name = f"{output_prefix}_{TODAY}.pdf"
    q2 = (f"name='{pdf_name}' and '{day_id}' in parents and trashed=false")
    res2 = svc.files().list(q=q2, fields="files(id,name,webViewLink,size,createdTime)",
                            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res2.get("files", [])
    if files: return files[0]
    return None

def main():
    svc = drive_service()
    output_prefix = os.environ.get("OUTPUT_PREFIX", "ETIQUETAS")
    force_regen = os.environ.get("FORCE_REGEN") == "1"
    emitted, emitted_fid, _ = drive_load_or_bootstrap_emitted(svc, output_prefix)
    emitted_shipments = emitted.setdefault("shipments", {})

    # FORCE_REGEN permite rehacer solo el día actual, nunca vuelve a habilitar
    # shipment IDs que ya aparecieron en PDFs de días anteriores.
    if force_regen:
        today_ids = [sid for sid, meta in emitted_shipments.items()
                     if (meta or {}).get("date") == TODAY]
        for sid in today_ids:
            emitted_shipments.pop(sid, None)
        if today_ids:
            emitted["updated_at"] = datetime.now(TZ).isoformat()
            drive_save_json(svc, LEDGER_NAME, emitted, emitted_fid)
            print(f"[force] liberé {len(today_ids)} guías emitidas hoy")

    # Guard: si el PDF de hoy ya existe, salir limpio (idempotencia para multi-cron)
    # Override con FORCE_REGEN=1: borra el viejo y regenera
    if force_regen:
        existing = already_done_today(svc)
        if existing:
            try:
                svc.files().delete(fileId=existing["id"], supportsAllDrives=True).execute()
                print(f"[force] Borré PDF previo de hoy: {existing.get('name')}")
            except Exception as e:
                print(f"[force] No pude borrar viejo: {e}")
        existing = None
    else:
        existing = already_done_today(svc)
    if existing:
        msg = (f"🤖 <b>Etiquetas {TODAY}</b>\n"
               f"⏭ Ya existían — skip\n"
               f"<a href=\"{existing.get('webViewLink','')}\">📄 PDF existente</a> "
               f"({int(int(existing.get('size','0'))/1024)} KB)")
        print(msg)
        tg_send(msg)
        return
    stats, stats_fid = drive_find_or_get_stats(svc)
    report = [f"🤖 <b>Etiquetas diarias</b> · {TODAY}", ""]
    summary = {}
    any_error = False
    all_ships = []
    per_account_counts = {}

    # 1) Recolectar shipments de las cuentas seleccionadas
    account_filter = {x.strip().lower() for x in os.environ.get("ACCOUNT_FILTER", "").split(",") if x.strip()}
    selected_accounts = [a for a in ACCOUNTS if not account_filter or a["name"].lower() in account_filter]
    for account in selected_accounts:
        nm = account["name"]
        print(f"\n========== {nm} ==========")
        try:
            at, err = validate_account(account)
            if err:
                msg = f"❌ <b>{nm}</b>: {err}"
                report.append(msg); print(msg); any_error = True
                per_account_counts[nm] = 0; continue
            ships = collect_shipments(at, account)
            scanned_n = len(ships)
            # SIN dedupe global: incluir TODAS las accionables cada día.
            # Mientras el vendedor no haya entregado el paquete en agencia (substatus != picked_up),
            # la guía debe reaparecer todos los días. El ledger sigue registrando para auditoría.
            n = len(ships)
            skipped_n = 0
            per_account_counts[nm] = n
            print(f"  shipments accionables: {scanned_n} (todas incluidas — sin dedupe global)")
            prev = stats.get(nm, {}).get("last_count")
            anomaly = ""
            if prev is not None and prev > 5:
                if n == 0:
                    anomaly = f"⚠ AYER tenía {prev}, hoy 0"
                elif n < prev * 0.30:
                    anomaly = f"⚠ Caída brusca: ayer {prev} → hoy {n}"
                elif n > prev * 5 and n > 50:
                    anomaly = f"⚠ Subida atípica: ayer {prev} → hoy {n}"
            if anomaly:
                report.append(f"   {nm}: {anomaly}")
            all_ships.extend(ships)
            summary[nm] = {"last_count":n,"date":TODAY}
        except Exception as e:
            print(traceback.format_exc())
            report.append(f"❌ <b>{nm}</b>: excepción {type(e).__name__}: {str(e)[:140]}")
            any_error = True
            per_account_counts[nm] = 0

    if not all_ships:
        for nm, n in per_account_counts.items():
            report.append(f"📭 <b>{nm}</b>: {n} pendientes")
        report.append("\nNo hay etiquetas para subir.")
        new_stats = dict(stats); new_stats.update(summary); new_stats["__last_run"] = TODAY
        try: drive_save_stats(svc, new_stats, stats_fid)
        except Exception as e: report.append(f"⚠ stats fail: {str(e)[:80]}")
        tg_send("\n".join(report))
        print("\n".join(report))
        if any_error: sys.exit(1)
        return

    # 2) Dedupe defensivo global por shipment ID y orden del PDF.
    unique_ships = {}
    for ship in all_ships:
        unique_ships.setdefault(str(ship["sid"]), ship)
    duplicated_in_run = len(all_ships) - len(unique_ships)
    if duplicated_in_run:
        print(f"[dedupe] {duplicated_in_run} shipment IDs repetidos omitidos dentro de la ejecución")
    all_ships = list(unique_ships.values())
    all_ships.sort(key=lambda s: (s["account"], 0 if s["has_used"] else 1,
                                  "/".join(s["comp_lines"]), s["sid"]))

    # 3) Construir UN PDF combinado
    total = len(all_ships)
    breakdown = " + ".join(f"{nm}:{n}" for nm,n in per_account_counts.items())
    print(f"\n========== PDF combinado: {total} envíos ({breakdown}) ==========")
    out_local = f"{output_prefix}_{TODAY}.pdf"
    pages, fails = build_pdf(all_ships, out_local)
    if pages == 0:
        report.append(f"❌ PDF salió vacío (fallidas {len(fails)}). NO subo.")
        any_error = True
    else:
        try:
            # Reconstruye cliente Drive: el socket original puede llevar 10-20 min
            # inactivo mientras se recolectan shipments de MELI y muere con SSL EOF.
            def _fresh_svc():
                for _att in range(1, 4):
                    try:
                        return drive_service()
                    except Exception as _e:
                        print(f"[drive] rebuild attempt {_att} fail: {type(_e).__name__}: {str(_e)[:120]}")
                        import time as _t; _t.sleep(3*_att)
                return drive_service()  # last try, propaga si truena
            svc = _fresh_svc()

            # Retry SSL EOF en find/create day folder
            import ssl as _ssl
            day_folder_id = None
            for _att in range(1, 5):
                try:
                    day_folder_id = drive_find_or_create_day_folder(svc, DRIVE_FOLDER_ID, TODAY)
                    break
                except (_ssl.SSLEOFError, _ssl.SSLError, ConnectionError, OSError) as _e:
                    print(f"[drive] day_folder attempt {_att} SSL/net fail: {type(_e).__name__}: {str(_e)[:120]}")
                    import time as _t; _t.sleep(2*_att)
                    svc = _fresh_svc()
            if day_folder_id is None:
                raise RuntimeError("drive_find_or_create_day_folder falló tras 4 reintentos")

            up = drive_upload_pdf(svc, out_local, out_local, day_folder_id)
            file_link = up.get("webViewLink", "")

            # El registro se confirma únicamente después de que Drive recibió el PDF.
            # Si guardar el registro falla, se elimina el PDF para evitar que mañana
            # esas mismas guías se vuelvan a imprimir sin control.
            failed_ids = {str(sid) for sid in fails}
            for ship in all_ships:
                sid = str(ship["sid"])
                if sid not in failed_ids:
                    emitted_shipments[sid] = {
                        "date": TODAY, "account": ship["account"],
                        "source_file_id": up["id"]
                    }
            emitted["updated_at"] = datetime.now(TZ).isoformat()
            try:
                drive_save_json(svc, LEDGER_NAME, emitted, emitted_fid)
            except Exception as ledger_error:
                try:
                    svc.files().delete(fileId=up["id"], supportsAllDrives=True).execute()
                except Exception:
                    pass
                raise RuntimeError(f"No se pudo guardar control anti-repetidos: {ledger_error}")

            # En el flujo unificado, los PDFs separados del mismo día se mandan
            # a la papelera solo después de confirmar el consolidado.
            if output_prefix == "ETIQUETAS_UNIFICADAS":
                legacy_names = {
                    f"ETIQUETAS_{TODAY}.pdf",
                    f"ETIQUETAS_EDILBERTO_LUISED_{TODAY}.pdf",
                }
                for legacy_name in legacy_names:
                    safe_legacy = legacy_name.replace("'", "\\'")
                    old_files = svc.files().list(
                        q=f"name='{safe_legacy}' and '{day_folder_id}' in parents and trashed=false",
                        fields="files(id,name)", pageSize=100,
                        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                    for old_file in old_files.get("files", []):
                        svc.files().update(
                            fileId=old_file["id"], body={"trashed": True},
                            supportsAllDrives=True).execute()
                        print(f"[unified] separado enviado a papelera: {old_file['name']}")

            day_folder_link = f"https://drive.google.com/drive/folders/{day_folder_id}"
            report.append(f"✅ <b>PDF combinado</b>: {pages} págs ({total} envíos · {len(fails)} fallidas)")
            report.append(f"🔒 Control anti-repetidos actualizado: {len(emitted_shipments)} guías registradas")
            for nm, n in per_account_counts.items():
                report.append(f"   • {nm}: {n}")
            report.append(f"\n📂 <a href=\"{day_folder_link}\">Carpeta {TODAY}</a>")
            report.append(f"📄 <a href=\"{file_link}\">Abrir PDF directo</a>")
            summary["__combined"] = {"pages":pages, "file_id":up["id"], "date":TODAY,
                                    "day_folder_id":day_folder_id,
                                    "breakdown":per_account_counts}
        except Exception as e:
            print(traceback.format_exc())
            report.append(f"❌ Upload falló: {type(e).__name__}: {str(e)[:140]}")
            any_error = True

    # 4) Persiste stats
    new_stats = dict(stats); new_stats.update(summary); new_stats["__last_run"] = TODAY
    try:
        drive_save_stats(svc, new_stats, stats_fid)
    except Exception as e:
        report.append(f"⚠ No pude guardar stats.json: {str(e)[:120]}")
    folder_link = f"https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}"
    report.append("")
    report.append(f"📁 <a href=\"{folder_link}\">Carpeta raíz</a>")
    tg_send("\n".join(report))
    print("\n=== TELEGRAM REPORT ===")
    print("\n".join(report))
    if any_error:
        sys.exit(1)

if __name__ == "__main__":
    main()


