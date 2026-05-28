"""Crea subcarpeta YYYY-MM-DD del día dentro del parent y mueve el PDF de hoy adentro."""
import os, sys
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TZ = timezone(timedelta(hours=-6))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")
PARENT = "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL"
SCOPES = ["https://www.googleapis.com/auth/drive"]

creds = Credentials(
    token=None,
    refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
    scopes=SCOPES,
)
creds.refresh(Request())
svc = build("drive", "v3", credentials=creds, cache_discovery=False)

# 1) Find or create today's subfolder
q = (f"name='{TODAY}' and mimeType='application/vnd.google-apps.folder' "
     f"and '{PARENT}' in parents and trashed=false")
res = svc.files().list(q=q, fields="files(id,name)").execute()
files = res.get("files", [])
if files:
    day_id = files[0]["id"]
    print(f"[OK] Subcarpeta {TODAY} ya existía: {day_id}")
else:
    f = svc.files().create(
        body={"name": TODAY, "mimeType": "application/vnd.google-apps.folder",
              "parents": [PARENT]},
        fields="id,name,webViewLink"
    ).execute()
    day_id = f["id"]
    print(f"[OK] Subcarpeta {TODAY} creada: {day_id}  ({f.get('webViewLink')})")

# 2) Mover el PDF de hoy desde raíz a la subcarpeta
pdf_name = f"ETIQUETAS_{TODAY}.pdf"
q2 = f"name='{pdf_name}' and '{PARENT}' in parents and trashed=false"
files2 = svc.files().list(q=q2, fields="files(id,name,parents)").execute().get("files", [])
if not files2:
    print(f"[OK] No hay '{pdf_name}' en raíz para mover (puede ser que ya esté en subcarpeta).")
else:
    for f in files2:
        fid = f["id"]
        # Quita parent raíz y agrega parent del día
        svc.files().update(
            fileId=fid,
            addParents=day_id,
            removeParents=PARENT,
            fields="id,parents"
        ).execute()
        print(f"[OK] '{pdf_name}' movido a {TODAY}/ (file_id={fid})")

# 3) Verificación: listar contenido de la subcarpeta
res = svc.files().list(q=f"'{day_id}' in parents and trashed=false",
                       fields="files(id,name,size)").execute()
print(f"\nContenido de {TODAY}/:")
for f in res.get("files", []):
    print(f"  - {f.get('name')} ({f.get('size','?')} bytes)")
