import os, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
                    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
                    scopes=["https://www.googleapis.com/auth/drive"])
creds.refresh(Request())
svc = build("drive","v3",credentials=creds,cache_discovery=False)
PARENT = "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL"
# List ALL items in parent
res = svc.files().list(q=f"'{PARENT}' in parents and trashed=false",
                       fields="files(id,name,mimeType,createdTime)").execute()
print(f"=== Contenido de carpeta raíz ===")
for f in res.get("files", []):
    print(f"  {f.get('mimeType','?'):50} {f.get('name'):40} {f.get('createdTime','')}")
# Buscar específicamente 2026-06-08
print("\n=== Búsqueda por nombre ===")
res2 = svc.files().list(q=f"name contains '2026-06-08' and trashed=false",
                       fields="files(id,name,parents,createdTime)").execute()
for f in res2.get("files", []):
    print(f"  {f.get('name'):40} parents={f.get('parents')} {f.get('createdTime','')}")
