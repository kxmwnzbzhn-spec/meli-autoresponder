#!/usr/bin/env python3
"""
Sube las etiquetas del día a Google Drive.

USA OAuth USER DELEGATION (no Service Account) para evitar
"Service Accounts do not have storage quota" en Drive personal.

Requiere los siguientes env vars (GitHub secrets):
- GOOGLE_OAUTH_CLIENT_ID      ← OAuth Desktop client del usuario
- GOOGLE_OAUTH_CLIENT_SECRET
- GOOGLE_OAUTH_REFRESH_TOKEN  ← refresh_token obtenido tras autorizar

Fallback: si las 3 vars OAuth no están pero hay GOOGLE_SERVICE_ACCOUNT_JSON,
intenta con SA (solo funciona en Shared Drives).

- Carpeta padre: ETIQUETAS (debe existir y ser propiedad del usuario)
- Subcarpeta por fecha: YYYY-MM-DD
- Sube todos los .pdf + manifest.xlsx + el TODAS_*.pdf
"""
import os, sys, json, glob
from datetime import datetime, timezone, timedelta

try:
    from google.oauth2.credentials import Credentials as UserCredentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Falta paquete: pip install google-api-python-client google-auth")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive"]
PARENT_NAME = os.environ.get("LABELS_FOLDER_NAME", "ETIQUETAS")
TOKEN_URI   = "https://oauth2.googleapis.com/token"


def get_service():
    """Devuelve un Drive service. Prioriza OAuth user; si no, SA."""
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    rt = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")

    if cid and csec and rt:
        print("[auth] usando OAuth user delegation")
        creds = UserCredentials(
            token=None,
            refresh_token=rt,
            token_uri=TOKEN_URI,
            client_id=cid,
            client_secret=csec,
            scopes=SCOPES,
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        print("[auth] usando Service Account (fallback - solo Shared Drives)")
        info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    raise RuntimeError(
        "No hay credenciales: define GOOGLE_OAUTH_REFRESH_TOKEN "
        "(+ CLIENT_ID/SECRET) o GOOGLE_SERVICE_ACCOUNT_JSON"
    )


def find_or_create_folder(svc, name, parent_id=None):
    q = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = svc.files().list(
        q=q, fields="files(id,name)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    f = svc.files().create(body=body, fields="id", supportsAllDrives=True).execute()
    return f["id"]


def upload_file(svc, fp, parent_id):
    fname = os.path.basename(fp)
    if fp.endswith(".pdf"):
        mime = "application/pdf"
    elif fp.endswith(".xlsx"):
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif fp.endswith(".csv"):
        mime = "text/csv"
    else:
        mime = "application/octet-stream"
    media = MediaFileUpload(fp, mimetype=mime, resumable=True)
    body = {"name": fname, "parents": [parent_id]}
    f = svc.files().create(
        body=body, media_body=media,
        fields="id,name,webViewLink",
        supportsAllDrives=True,
    ).execute()
    return f


def main():
    # Localizar carpeta de hoy
    cdmx = timezone(timedelta(hours=-6))
    today_cdmx = datetime.now(cdmx).strftime("%Y-%m-%d")

    # Buscar carpeta local labels_pending_*
    candidates = sorted(glob.glob(f"labels_pending_{today_cdmx}_*"))
    if not candidates:
        candidates = sorted(glob.glob("labels_pending_*"))
    if not candidates:
        print("No hay carpeta labels_pending_* para subir")
        return

    src = candidates[-1]  # más reciente
    print(f"📦 Subiendo desde {src}/")

    svc = get_service()
    parent_id = find_or_create_folder(svc, PARENT_NAME)
    print(f"📁 Carpeta padre '{PARENT_NAME}': {parent_id}")
    date_folder_id = find_or_create_folder(svc, today_cdmx, parent_id)
    print(f"📁 Subcarpeta '{today_cdmx}': {date_folder_id}")

    files_to_upload = sorted(glob.glob(os.path.join(src, "*")))
    # También subir el TODAS_*.pdf (mergeado) si existe en raíz
    todas = sorted(glob.glob(f"TODAS_{src}*.pdf"))
    files_to_upload.extend(todas)

    uploaded = []
    for fp in files_to_upload:
        if os.path.isdir(fp):
            continue
        try:
            r = upload_file(svc, fp, date_folder_id)
            uploaded.append(r)
            _name = r["name"]
            print(f"  ✅ {_name}")
        except Exception as e:
            print(f"  ❌ {fp}: {e}")

    print(f"\n✅ {len(uploaded)} archivos subidos a Drive/{PARENT_NAME}/{today_cdmx}/")

    # Telegram opcional
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat and uploaded:
        import requests
        link = f"https://drive.google.com/drive/folders/{date_folder_id}"
        msg = (
            f"📤 Etiquetas {today_cdmx} subidas a Drive\n"
            f"{len(uploaded)} archivos\n{link}"
        )
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                data={"chat_id": tg_chat, "text": msg},
                timeout=20,
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
