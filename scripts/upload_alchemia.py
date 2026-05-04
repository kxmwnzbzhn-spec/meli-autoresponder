"""Sube alchemia_lab_catalog.xlsx a Drive en carpeta ALCHEMIA_LAB."""
import os, sys
from google.oauth2.credentials import Credentials as UC
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

cid=os.environ["GOOGLE_OAUTH_CLIENT_ID"]
csec=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
rt=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"]
creds=UC(token=None,refresh_token=rt,token_uri="https://oauth2.googleapis.com/token",
    client_id=cid,client_secret=csec,scopes=["https://www.googleapis.com/auth/drive"])
svc=build("drive","v3",credentials=creds,cache_discovery=False)

def find_or_create(name, parent=None):
    q=f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent: q+=f" and '{parent}' in parents"
    r=svc.files().list(q=q,fields="files(id,name)").execute().get("files",[])
    if r: return r[0]["id"]
    body={"name":name,"mimeType":"application/vnd.google-apps.folder"}
    if parent: body["parents"]=[parent]
    return svc.files().create(body=body,fields="id").execute()["id"]

folder_id = find_or_create("ALCHEMIA_LAB")
print(f"📁 ALCHEMIA_LAB: {folder_id}")

# Si ya existe el xlsx, borrarlo primero para evitar duplicado
existing=svc.files().list(q=f"name='alchemia_lab_catalog.xlsx' and '{folder_id}' in parents and trashed=false",
                          fields="files(id)").execute().get("files",[])
for f in existing:
    svc.files().update(fileId=f["id"],body={"trashed":True}).execute()

# Upload
fp = "alchemia_lab_catalog.xlsx"
media=MediaFileUpload(fp,mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",resumable=True)
body={"name":"alchemia_lab_catalog.xlsx","parents":[folder_id]}
f=svc.files().create(body=body,media_body=media,fields="id,name,webViewLink").execute()
print(f"✅ Subido: {f['name']} → {f['webViewLink']}")
print(f"\n🔗 Folder: https://drive.google.com/drive/folders/{folder_id}")
