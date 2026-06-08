"""Borra el PDF de prueba que generé hoy y la subcarpeta vacía si queda."""
import os, sys, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
TODAY = "2026-06-08"
PARENT = "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL"
creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
                    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
                    scopes=["https://www.googleapis.com/auth/drive"])
creds.refresh(Request())
svc = build("drive","v3",credentials=creds,cache_discovery=False)
# Find subcarpeta del día
q = f"name='{TODAY}' and '{PARENT}' in parents and trashed=false"
res = svc.files().list(q=q, fields="files(id,name)").execute()
files = res.get("files", [])
if not files:
    print(f"No existe subcarpeta {TODAY}"); sys.exit(0)
day_id = files[0]["id"]
# List PDFs inside
q2 = f"'{day_id}' in parents and trashed=false"
inside = svc.files().list(q=q2, fields="files(id,name)").execute().get("files", [])
print(f"Subcarpeta {TODAY} tiene {len(inside)} archivos:")
for f in inside:
    print(f"  - {f['name']}")
    svc.files().delete(fileId=f["id"]).execute()
    print(f"    borrado")
# Borrar carpeta vacía
svc.files().delete(fileId=day_id).execute()
print(f"Subcarpeta {TODAY} borrada")
