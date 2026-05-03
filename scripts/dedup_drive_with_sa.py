#!/usr/bin/env python3
"""DEDUP Drive con SA fallback: si OAuth no tiene perms (carpetas viejas
creadas por SA), usa SA para borrarlas."""
import os, json, sys, re
from google.oauth2.credentials import Credentials as UC
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]
KEEP_DAYS = int(os.environ.get("KEEP_DAYS","1"))

# OAuth user
oauth_creds = UC(
    token=None,
    refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
    scopes=SCOPES,
)
oauth_svc = build("drive","v3",credentials=oauth_creds,cache_discovery=False)

# SA fallback
sa_svc = None
sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if sa_json:
    info = json.loads(sa_json)
    sa_creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    sa_svc = build("drive","v3",credentials=sa_creds,cache_discovery=False)
    print(f"[SA] disponible: {info.get('client_email')}")
else:
    print("[SA] no disponible")


def find_folder(svc, name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent: q += f" and '{parent}' in parents"
    r = svc.files().list(q=q, fields="files(id,name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    return (r.get("files",[]) or [{}])[0].get("id")


def list_all(svc, parent_id):
    out, page = [], None
    while True:
        r = svc.files().list(q=f"'{parent_id}' in parents and trashed=false",
            fields="nextPageToken,files(id,name,mimeType,owners(emailAddress))",
            pageSize=1000, pageToken=page,
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        out.extend(r.get("files",[]))
        page = r.get("nextPageToken")
        if not page: break
    return out


parent_id = find_folder(oauth_svc, "ETIQUETAS")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
date_folders = sorted(
    [i for i in list_all(oauth_svc, parent_id)
     if i["mimeType"]=="application/vnd.google-apps.folder" and DATE_RE.match(i["name"])],
    key=lambda x: x["name"]
)
keep = date_folders[-KEEP_DAYS:]
delete = date_folders[:-KEEP_DAYS]
print(f"\nKEEP: {[f['name'] for f in keep]}")
print(f"DELETE: {[f['name'] for f in delete]}")

deleted_ok = 0
errs = []

for df in delete:
    owners = df.get("owners",[])
    owner_email = owners[0]["emailAddress"] if owners else "?"
    print(f"\n  {df['name']} owner={owner_email}")

    # Intentar OAuth primero
    try:
        oauth_svc.files().update(fileId=df["id"], body={"trashed":True}, supportsAllDrives=True).execute()
        print(f"    🗑️ OAuth borró")
        deleted_ok += 1
        continue
    except Exception as e:
        msg = str(e)[:120]
        print(f"    OAuth falló: {msg[:80]}")

    # SA fallback (recursivo: para borrar via SA hay que ir hacia adentro)
    if sa_svc:
        try:
            # SA deletes children first then folder
            children = list_all(sa_svc, df["id"])
            for c in children:
                try:
                    sa_svc.files().delete(fileId=c["id"], supportsAllDrives=True).execute()
                except Exception as ce:
                    print(f"       child {c['name']}: err {str(ce)[:60]}")
            sa_svc.files().delete(fileId=df["id"], supportsAllDrives=True).execute()
            print(f"    🗑️ SA borró")
            deleted_ok += 1
            continue
        except Exception as e:
            errs.append({"folder":df["name"],"err":str(e)[:100]})
            print(f"    SA también falló: {str(e)[:80]}")
    else:
        errs.append({"folder":df["name"],"err":"no SA disponible y OAuth sin perms"})

print(f"\n=== RESUMEN ===")
print(f"Borradas: {deleted_ok}/{len(delete)}")
print(f"Errores: {len(errs)}")
for e in errs: print(f"  {e}")

TG = os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID = os.environ.get("TELEGRAM_CHAT_ID","")
if TG and TGCID:
    import requests
    msg = f"🧹 *Drive ETIQUETAS limpio* (SA fallback)\n\n"
    msg += f"📁 Conservada: {keep[0]['name'] if keep else '?'}\n"
    msg += f"🗑️ Borradas: *{deleted_ok}*\n"
    if errs:
        msg += f"❌ Errores: *{len(errs)}*\n"
        for e in errs[:5]:
            msg += f"  • {e['folder']}: {e['err'][:60]}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
