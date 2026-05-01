#!/usr/bin/env python3
"""
Sube las etiquetas del día a Google Drive.
- Carpeta padre: ETIQUETAS (compartida con Service Account)
- Subcarpeta por fecha: YYYY-MM-DD
- Sube todos los .pdf + manifest.xlsx + el TODAS_*.pdf

Requiere:
- GOOGLE_SERVICE_ACCOUNT_JSON env var (contenido completo del JSON)
- LABELS_FOLDER_NAME (default: ETIQUETAS)
"""
import os, sys, json, glob
from datetime import datetime, timezone, timedelta

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Falta paquete: pip install google-api-python-client google-auth")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive"]
PARENT_NAME = os.environ.get("LABELS_FOLDER_NAME", "ETIQUETAS")

def get_service():
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def find_or_create_folder(svc, name, parent=None):
    q = f"name = {name!r} and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent:
        q += f" and {parent!r} in parents"
    res = svc.files().list(q=q, fields="files(id,name)", pageSize=10, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        body["parents"] = [parent]
    folder = svc.files().create(body=body, fields="id", supportsAllDrives=True).execute()
    return folder["id"]

def upload_file(svc, local_path, parent_id):
    name = os.path.basename(local_path)
    media = MediaFileUpload(local_path, resumable=False)
    body = {"name": name, "parents": [parent_id]}
    f = svc.files().create(body=body, media_body=media, fields="id,name,webViewLink", supportsAllDrives=True).execute()
    return f

def main():
    svc = get_service()

    # Carpeta padre
    parent_id = find_or_create_folder(svc, PARENT_NAME)
    print(f"📁 Carpeta padre {PARENT_NAME!r}: {parent_id}")

    # Subcarpeta de fecha (YYYY-MM-DD CDMX)
    today_cdmx = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d")
    date_folder_id = find_or_create_folder(svc, today_cdmx, parent=parent_id)
    print(f"📁 Subcarpeta {today_cdmx!r}: {date_folder_id}")

    # Buscar archivos a subir
    label_dirs = sorted(glob.glob("labels_pending_*"), reverse=True)
    if not label_dirs:
        print("⚠️ No hay carpeta labels_pending_* — nada que subir")
        return
    label_dir = label_dirs[0]
    print(f"📦 Subiendo desde {label_dir}/")

    files_to_upload = []
    for f in sorted(glob.glob(f"{label_dir}/*.pdf") + glob.glob(f"{label_dir}/*.xlsx")):
        files_to_upload.append(f)
    # Tambien el TODAS combinado en raiz
    todas = glob.glob("TODAS_labels_pending_*.pdf")
    files_to_upload.extend(sorted(todas, reverse=True)[:1])

    uploaded = []
    for fp in files_to_upload:
        try:
            r = upload_file(svc, fp, date_folder_id)
            uploaded.append(r)
            print(f"  ✅ {r[\"name\"]}")
        except Exception as e:
            print(f"  ❌ {fp}: {e}")

    print(f"\\n✅ {len(uploaded)} archivos subidos a Drive/{PARENT_NAME}/{today_cdmx}/")

    # Telegram opcional
    tg_t = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_c = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_t and tg_c and uploaded:
        import urllib.request, urllib.parse
        link = f"https://drive.google.com/drive/folders/{date_folder_id}"
        msg = f"📤 Etiquetas {today_cdmx} subidas a Drive\\n{len(uploaded)} archivos\\n{link}"
        try:
            urllib.request.urlopen(
                f"https://api.telegram.org/bot{tg_t}/sendMessage",
                data=urllib.parse.urlencode({"chat_id":tg_c,"text":msg}).encode(),
                timeout=10
            )
        except: pass

if __name__ == "__main__":
    main()

