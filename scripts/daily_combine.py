"""Combina los 3 PDFs por cuenta, filtra excluidos, sube a Drive del día.
Llamado por el job 'combine-and-upload' del workflow daily_pro.yml.

Excluye (SID-based de manifest + text-based del PDF):
  - Bose Soundlink Home Negro (varios SIDs, color = None en variation_attributes)
  - Club de Nuit Malek / Maleka / Malaka
  - Armaf (cualquier)
  - Angel Nova
  - Alma de Tenochtitlán (acentos normalizados)
"""
import os, re, sys, json, requests, glob, traceback, unicodedata, time
from datetime import datetime, timezone, timedelta
from pypdf import PdfReader, PdfWriter

TZ = timezone(timedelta(hours=-6))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")
DRIVE_FOLDER = os.environ.get("DRIVE_FOLDER_ID", "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "")
FORCE = os.environ.get("FORCE_REGEN") == "1"
MANIFEST_URL = "https://raw.githubusercontent.com/kxmwnzbzhn-spec/meli-autoresponder/main/data/manifest.json"

# Exclusión hardcoded
EXCL_KEYWORDS = [
    'club de nuit','armaf','malek','maleka','malaka',
    'angel nova','alma de tenochtitlan',
]

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def is_bad_text(text):
    tl = strip_accents(text.lower())
    if 'bose' in tl and ('negr' in tl or 'black' in tl): return True
    return any(k in tl for k in EXCL_KEYWORDS)

def tg_send(text):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": "true"}, timeout=10)
    except: pass

def get_excluded_sids():
    """Read manifest and return SIDs that match exclusion criteria (catches Bose Negro
    where label text doesn't say 'negro')."""
    sids = set()
    try:
        r = requests.get(MANIFEST_URL + "?b=" + str(int(time.time())), timeout=20)
        d = r.json()
        for s in d.get('shipments', []):
            for p in s.get('products', []):
                t = strip_accents((p.get('title_full','') + ' ' + p.get('name_short','')).lower())
                if 'bose' in t and ('negr' in t or 'black' in t): sids.add(s['sid_str']); break
                if any(k in t for k in EXCL_KEYWORDS): sids.add(s['sid_str']); break
        print(f"[manifest] {len(sids)} SIDs en lista de exclusión (de {d.get('total')} shipments totales)")
    except Exception as e:
        print(f"[manifest fail] {e}")
    return sids

def drive_service():
    """OAuth user. SA solo como fallback."""
    from googleapiclient.discovery import build
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    cid  = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    rt   = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")
    if cid and csec and rt:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials(token=None, refresh_token=rt,
                            token_uri="https://oauth2.googleapis.com/token",
                            client_id=cid, client_secret=csec, scopes=SCOPES)
        creds.refresh(Request())
        svc = build("drive", "v3", credentials=creds, cache_discovery=False)
        svc.files().get(fileId=DRIVE_FOLDER, fields="id", supportsAllDrives=True).execute()
        print("[drive] auth=OAuth")
        return svc
    raise RuntimeError("Faltan credenciales OAuth de Drive")

def find_or_create_day_folder(svc):
    q = (f"name='{TODAY}' and mimeType='application/vnd.google-apps.folder' "
         f"and '{DRIVE_FOLDER}' in parents and trashed=false")
    res = svc.files().list(q=q, fields="files(id,name)",
                           supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res.get("files", [])
    if files:
        print(f"[drive] subcarpeta {TODAY} ya existe: {files[0]['id']}")
        return files[0]["id"]
    f = svc.files().create(body={"name": TODAY,
                                  "mimeType": "application/vnd.google-apps.folder",
                                  "parents": [DRIVE_FOLDER]},
                           fields="id", supportsAllDrives=True).execute()
    print(f"[drive] subcarpeta {TODAY} creada: {f['id']}")
    return f["id"]

def already_done(svc, day_id):
    """¿Ya existe ETIQUETAS_<TODAY>.pdf en la subcarpeta del día?"""
    q = (f"name contains 'ETIQUETAS_{TODAY}' and '{day_id}' in parents and trashed=false "
         f"and mimeType='application/pdf'")
    res = svc.files().list(q=q, fields="files(id,name,webViewLink,size)",
                           supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res.get("files", [])
    if files: return files[0]
    return None

def upload_pdf(svc, local_path, drive_name, parent_id, max_retries=6):
    """Upload resumable con backoff exponencial."""
    from googleapiclient.http import MediaFileUpload
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            media = MediaFileUpload(local_path, mimetype="application/pdf",
                                    resumable=True, chunksize=1024*1024)
            req = svc.files().create(
                body={"name": drive_name, "parents": [parent_id]},
                media_body=media, supportsAllDrives=True,
                fields="id,name,webViewLink")
            resp = None
            while resp is None:
                _, resp = req.next_chunk(num_retries=4)
            return resp
        except Exception as e:
            last_err = e
            print(f"  upload attempt {attempt}/{max_retries}: {type(e).__name__}: {str(e)[:200]}", flush=True)
            time.sleep(min(60, 2 ** attempt))
    raise last_err


def main():
    print(f"=== daily_combine para {TODAY} ===")
    # 1) Auth a Drive (early-fail si token vencido)
    try:
        svc = drive_service()
    except Exception as e:
        msg = (f"🚨 <b>daily_pro {TODAY}</b>: Token Drive vencido o inválido.\n"
               f"<code>{type(e).__name__}: {str(e)[:200]}</code>\n\n"
               f"Renueva en: https://github.com/kxmwnzbzhn-spec/meli-autoresponder/actions"
               f" (avísame y te paso URL OAuth)")
        print(msg); tg_send(msg); sys.exit(2)

    day_id = find_or_create_day_folder(svc)

    # 2) Idempotencia
    existing = already_done(svc, day_id)
    if existing and not FORCE:
        msg = (f"✅ <b>daily_pro {TODAY}</b>: ya existía PDF de hoy, skip.\n"
               f"<a href=\"{existing.get('webViewLink','')}\">📄 {existing.get('name','')}</a>")
        print(msg); tg_send(msg); return

    # 3) Filtros: SID-based + text-based
    sid_excl = get_excluded_sids()

    # 4) Combinar los 3 PDFs
    writer = PdfWriter()
    per_account = {}
    accounts = ["Claribel", "Asva", "Adrian"]
    # accounts → en la pipeline guardé como ETIQUETAS_Claribel.pdf, ETIQUETAS_Asva.pdf, ETIQUETAS_Ah.pdf
    # Mapeo display name → file name
    file_map = {"Claribel": "Claribel", "Asva": "Asva", "Adrian": "Ah"}
    for acc in accounts:
        fname = file_map[acc]
        # GitHub Actions download-artifact pone cada artifact en subdir con nombre del artifact
        candidates = [
            f"./pdfs/labels-{fname}/ETIQUETAS_{fname}.pdf",
            f"./pdfs/ETIQUETAS_{fname}.pdf",
        ]
        path = next((c for c in candidates if os.path.exists(c)), None)
        if not path:
            print(f"  [{acc}] PDF no encontrado en candidates {candidates}")
            per_account[acc] = {"in":0, "kept":0, "sid_excl":0, "text_excl":0}
            continue
        try:
            r = PdfReader(path)
            in_n = len(r.pages); kept = 0; se = 0; te = 0
            for page in r.pages:
                text = page.extract_text() or ""
                m = re.search(r'Ship[:\s]+(\d{10,})', text)
                sid = m.group(1) if m else None
                if sid and sid in sid_excl: se += 1; continue
                if is_bad_text(text): te += 1; continue
                writer.add_page(page); kept += 1
            per_account[acc] = {"in": in_n, "kept": kept, "sid_excl": se, "text_excl": te}
            print(f"  [{acc}] in={in_n} kept={kept} sid_excl={se} text_excl={te}")
        except Exception as e:
            print(f"  [{acc}] ERROR leyendo PDF: {e}")
            per_account[acc] = {"in":0, "kept":0, "sid_excl":0, "text_excl":0}

    total = len(writer.pages)
    if total == 0:
        msg = f"⚠ <b>daily_pro {TODAY}</b>: PDF resultante vacío. NO se sube nada."
        print(msg); tg_send(msg); sys.exit(1)

    out_name = f"ETIQUETAS_{TODAY}.pdf"
    with open(out_name, "wb") as f: writer.write(f)
    print(f"\n[combined] {total} págs · {os.path.getsize(out_name)} bytes")

    # 5) Upload a Drive
    try:
        # Si force_regen y existe versión vieja, borrarla
        if FORCE and existing:
            try:
                svc.files().delete(fileId=existing["id"], supportsAllDrives=True).execute()
                print(f"  [force] borré PDF previo: {existing.get('name')}")
            except Exception as e:
                print(f"  [force] no pude borrar viejo: {e}")
        up = upload_pdf(svc, out_name, out_name, day_id)
    except Exception as e:
        msg = (f"🚨 <b>daily_pro {TODAY}</b>: PDF generado ({total} págs) "
               f"pero upload Drive falló.\n<code>{type(e).__name__}: {str(e)[:200]}</code>")
        print(msg); tg_send(msg); sys.exit(3)

    # 6) Telegram report
    lines = [f"🤖 <b>daily_pro · {TODAY}</b>",
             f"📊 <b>{total}</b> págs entregadas"]
    for acc, st in per_account.items():
        lines.append(f"   • {acc}: {st['kept']} (in {st['in']}, excl SID {st['sid_excl']}, excl texto {st['text_excl']})")
    lines.append("")
    lines.append(f"📂 <a href=\"https://drive.google.com/drive/folders/{day_id}\">Carpeta {TODAY}</a>")
    lines.append(f"📄 <a href=\"{up.get('webViewLink','')}\">PDF</a>")
    tg_send("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        traceback.print_exc()
        tg_send(f"🚨 daily_pro {TODAY}: excepción no manejada: {type(e).__name__}: {str(e)[:200]}")
        sys.exit(1)
