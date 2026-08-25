import os,json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES=["https://www.googleapis.com/auth/drive"]
creds=Credentials(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"], scopes=SCOPES)
creds.refresh(Request())
svc=build("drive","v3",credentials=creds,cache_discovery=False)
FOLDER=os.environ["FOLDER_ID"]
r=svc.files().list(q=f"'{FOLDER}' in parents and trashed=false",
    fields="files(id,name,size,createdTime,modifiedTime,webViewLink,mimeType)",
    orderBy="createdTime desc", supportsAllDrives=True).execute()
for f in r.get("files",[]):
    if f.get("mimeType","").endswith("folder"): continue
    print(f"{f.get('createdTime')} | {int(f.get('size','0'))/1024:.1f}KB | {f['name']} | {f['id']}")
