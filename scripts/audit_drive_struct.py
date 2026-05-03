#!/usr/bin/env python3
"""Recorre toda la estructura de ETIQUETAS y muestra contenido."""
import os, sys
from google.oauth2.credentials import Credentials as UC
from googleapiclient.discovery import build

cid = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
csec = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
rt = os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"]
creds = UC(token=None, refresh_token=rt,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=cid, client_secret=csec,
    scopes=["https://www.googleapis.com/auth/drive"])
svc = build("drive","v3",credentials=creds,cache_discovery=False)


def find_folder(name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent: q += f" and '{parent}' in parents"
    r = svc.files().list(q=q, fields="files(id,name)").execute()
    files = r.get("files",[])
    return files[0]["id"] if files else None


def list_all(parent_id):
    out, page = [], None
    q = f"'{parent_id}' in parents and trashed=false"
    while True:
        r = svc.files().list(q=q, fields="nextPageToken,files(id,name,mimeType,size,modifiedTime)",
                             pageSize=1000, pageToken=page).execute()
        out.extend(r.get("files",[]))
        page = r.get("nextPageToken")
        if not page: break
    return out


parent_id = find_folder("ETIQUETAS")
print(f"ETIQUETAS id={parent_id}\n")

def walk(folder_id, depth=0, max_depth=3):
    items = list_all(folder_id)
    folders = [i for i in items if i["mimeType"] == "application/vnd.google-apps.folder"]
    files = [i for i in items if i["mimeType"] != "application/vnd.google-apps.folder"]
    pad = "  " * depth
    print(f"{pad}📁 ({len(folders)} carpetas, {len(files)} files)")
    for f in folders[:30]:
        print(f"{pad}  📂 {f['name']}")
        if depth < max_depth:
            walk(f["id"], depth+1, max_depth)
    if files:
        print(f"{pad}  primeros 5 files:")
        for f in files[:5]:
            sz = f.get("size","?")
            print(f"{pad}    📄 {f['name']} ({sz}B)")
    if len(folders) > 30:
        print(f"{pad}  ...+{len(folders)-30} más carpetas")


walk(parent_id)
