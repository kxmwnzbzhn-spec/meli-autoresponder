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
SB_URL = os.environ.get("SUPABASE_URL","").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY","")
RUN_ID = os.environ.get("GITHUB_RUN_ID","")
LOOKBACK_DAYS = 7  # SIDs entregados en últimos N días → SKIP (anti-duplicado)

# Exclusión hardcoded
EXCL_KEYWORDS = []  # Sin exclusiones automáticas — todo lo pendiente se imprime

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def is_bad_text(text):
    # Sin exclusiones automáticas. Si necesitas excluir algo puntualmente, hazlo manual.
    return False



# === SUPABASE TRACKING ===
def sb_already_delivered_sids(lookback_days=LOOKBACK_DAYS):
    """Devuelve set de SIDs ya entregados en los últimos N días."""
    if not (SB_URL and SB_KEY): return set()
    try:
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        cutoff = (_dt.now(_tz.utc) - _td(days=lookback_days)).date().isoformat()
        sids = set(); offset = 0
        while True:
            r = requests.get(f"{SB_URL}/rest/v1/etiquetas_entregadas",
                params={"select":"sid","batch_date":f"gte.{cutoff}","limit":1000,"offset":offset},
                headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=15)
            if r.status_code != 200: break
            rows = r.json()
            if not rows: break
            for row in rows: sids.add(row["sid"])
            if len(rows) < 1000: break
            offset += 1000
        print(f"[supabase] {len(sids)} SIDs ya entregados en últimos {lookback_days} días")
        return sids
    except Exception as e:
        print(f"[sb_already_delivered_sids] {e}")
    return set()

def sb_record_delivered(records):
    """Inserta (con upsert) los SIDs entregados en esta corrida."""
    if not (SB_URL and SB_KEY) or not records: return
    try:
        # Chunk de 500 para evitar payload demasiado grande
        for i in range(0, len(records), 500):
            chunk = records[i:i+500]
            r = requests.post(f"{SB_URL}/rest/v1/etiquetas_entregadas",
                json=chunk,
                headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                         "Content-Type":"application/json",
                         "Prefer":"resolution=merge-duplicates,return=minimal"}, timeout=30)
            if r.status_code not in (200, 201, 204):
                print(f"[sb_record] HTTP {r.status_code}: {r.text[:200]}")
        print(f"[supabase] registrados {len(records)} SIDs entregados")
    except Exception as e:
        print(f"[sb_record_delivered] {e}")

def sb_count_carryover(min_days=3):
    """Cuenta SIDs que llevan >N días en el sistema y siguen pendientes."""
    if not (SB_URL and SB_KEY): return 0
    try:
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        cutoff = (_dt.now(_tz.utc) - _td(days=min_days)).date().isoformat()
        r = requests.get(f"{SB_URL}/rest/v1/etiquetas_entregadas",
            params={"select":"sid","batch_date":f"lt.{cutoff}","limit":1},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Prefer":"count=exact"}, timeout=10)
        cnt = int(r.headers.get("content-range","0/0").split("/")[-1])
        return cnt
    except Exception as e:
        print(f"[sb_count_carryover] {e}")
    return 0

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

    # 4) Cargar SIDs ya entregados en últimos N días (anti-duplicado)
    already_delivered = sb_already_delivered_sids()

    # 5) Combinar los 3 PDFs
    writer = PdfWriter()
    per_account = {}
    delivered_records = []  # para INSERT batch al final
    today_cdmx = (datetime.now(TZ)).strftime("%Y-%m-%d")
    accounts = ["Claribel", "Asva", "Adrian"]
    artifact_map = {"Claribel": "Claribel", "Asva": "Asva", "Adrian": "Ah"}
    file_map     = {"Claribel": "CLARIBEL", "Asva": "ASVA", "Adrian": "AH"}
    for acc in accounts:
        adir = artifact_map[acc]; fname = file_map[acc]
        candidates = [
            f"./pdfs/labels-{adir}/ETIQUETAS_{fname}.pdf",
            f"./pdfs/ETIQUETAS_{fname}.pdf",
        ]
        path = next((c for c in candidates if os.path.exists(c)), None)
        if not path:
            print(f"  [{acc}] PDF no encontrado en candidates {candidates}")
            per_account[acc] = {"in":0, "kept":0, "sid_excl":0, "text_excl":0, "dup_excl":0}
            continue
        try:
            r = PdfReader(path)
            in_n = len(r.pages); kept = 0; se = 0; te = 0; du = 0
            for page in r.pages:
                text = page.extract_text() or ""
                m = re.search(r'Ship[:\s]+(\d{10,})', text)
                sid = m.group(1) if m else None
                if sid and sid in sid_excl: se += 1; continue
                if is_bad_text(text): te += 1; continue
                if sid and sid in already_delivered: du += 1; continue  # ANTI-DUPLICADO
                writer.add_page(page); kept += 1
                if sid:
                    # Extraer primera línea del producto del header del label como title
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    product_title = next((l for l in lines if any(c.isalpha() for c in l)), "")[:200]
                    delivered_records.append({
                        "sid": sid, "account": acc, "product_title": product_title,
                        "batch_date": today_cdmx,
                        "run_id": int(RUN_ID) if RUN_ID.isdigit() else None,
                    })
            per_account[acc] = {"in": in_n, "kept": kept, "sid_excl": se, "text_excl": te, "dup_excl": du}
            print(f"  [{acc}] in={in_n} kept={kept} sid_excl={se} text_excl={te} dup_excl={du}")
        except Exception as e:
            print(f"  [{acc}] ERROR leyendo PDF: {e}")
            per_account[acc] = {"in":0, "kept":0, "sid_excl":0, "text_excl":0, "dup_excl":0}

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

    # 6) Registrar SIDs entregados (anti-duplicado para próximas corridas)
    sb_record_delivered(delivered_records)

    # 7) Telegram report con carryover
    carryover = sb_count_carryover(3)
    lines = [f"🤖 <b>daily_pro · {TODAY}</b>",
             f"📊 <b>{total}</b> págs entregadas (sin duplicados)"]
    for acc, st in per_account.items():
        lines.append(f"   • {acc}: {st['kept']} (excl: {st['sid_excl']} SID, {st['text_excl']} texto, {st['dup_excl']} ya entregados)")
    if carryover > 0:
        lines.append(f"\n🚨 <b>{carryover} envíos en carryover</b> (>3 días en sistema, sin enviar físicamente)")
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
