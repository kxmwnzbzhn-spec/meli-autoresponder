#!/usr/bin/env python3
"""DEDUP Google Drive ETIQUETAS:
Recorre carpeta ETIQUETAS y todas sus subcarpetas YYYY-MM-DD.
Para cada shipment_id (hex prefix de _labels.pdf), si aparece en varias
fechas, conserva el archivo en la fecha mas TEMPRANA (cuando se generó por
primera vez) y elimina las copias de fechas posteriores.

DRY_RUN=1 → solo reporta, no borra.
"""
import os, sys, re
from collections import defaultdict
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials as UserCredentials
    from googleapiclient.discovery import build
except ImportError:
    print("pip install google-api-python-client google-auth"); sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive"]
PARENT_NAME = "ETIQUETAS"
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LABEL_RE = re.compile(r"^([0-9A-Fa-f]{16,40})_labels\.pdf$")


def get_service():
    cid = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    csec = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
    rt = os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"]
    creds = UserCredentials(token=None, refresh_token=rt,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cid, client_secret=csec, scopes=SCOPES)
    return build("drive","v3",credentials=creds,cache_discovery=False)


def find_folder(svc, name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent: q += f" and '{parent}' in parents"
    r = svc.files().list(q=q, fields="files(id,name)").execute()
    files = r.get("files",[])
    return files[0]["id"] if files else None


def list_children(svc, parent_id, mime=None, fields="files(id,name,modifiedTime,createdTime,size)"):
    out, page = [], None
    q = f"'{parent_id}' in parents and trashed=false"
    if mime: q += f" and mimeType='{mime}'"
    while True:
        r = svc.files().list(q=q, fields=f"nextPageToken,{fields}", pageSize=1000, pageToken=page).execute()
        out.extend(r.get("files",[]))
        page = r.get("nextPageToken")
        if not page: break
    return out


svc = get_service()
parent_id = find_folder(svc, PARENT_NAME)
if not parent_id:
    print(f"❌ Carpeta {PARENT_NAME} no encontrada")
    sys.exit(1)
print(f"ETIQUETAS folder id={parent_id}")

# Listar subcarpetas YYYY-MM-DD
date_folders = [f for f in list_children(svc, parent_id, mime="application/vnd.google-apps.folder")
                if DATE_RE.match(f["name"])]
date_folders.sort(key=lambda f: f["name"])
print(f"Date folders: {len(date_folders)}")
for f in date_folders:
    print(f"  {f['name']} ({f['id']})")

# Recolectar TODOS los _labels.pdf por shipment_id → list[(folder_date, file)]
by_ship = defaultdict(list)
total_files = 0
for df in date_folders:
    files = list_children(svc, df["id"], mime="application/pdf")
    for fi in files:
        m = LABEL_RE.match(fi["name"])
        if m:
            ship_id = m.group(1).upper()
            by_ship[ship_id].append({"date":df["name"],"file":fi})
            total_files += 1

print(f"\nTotal label PDFs: {total_files}")
print(f"Unique shipment IDs: {len(by_ship)}")

# Detectar duplicados
dups = {sid: lst for sid, lst in by_ship.items() if len(lst) > 1}
print(f"Shipment IDs duplicados: {len(dups)}")

deletes = []
keeps = []
for sid, lst in dups.items():
    # Sort por fecha ascendente. Conservar el primero (mas viejo).
    lst.sort(key=lambda x: x["date"])
    keeper = lst[0]
    losers = lst[1:]
    keeps.append({"sid":sid,"date":keeper["date"],"file_id":keeper["file"]["id"]})
    for L in losers:
        deletes.append({"sid":sid,"date":L["date"],"file_id":L["file"]["id"],
                        "name":L["file"]["name"],"size":L["file"].get("size")})

print(f"\n{'DRY RUN' if DRY_RUN else 'EJECUTANDO'} — eliminar {len(deletes)} archivos\n")

errors = []
for i, d in enumerate(deletes):
    if DRY_RUN:
        print(f"  [{i+1}/{len(deletes)}] DRY {d['sid']}: borrar de {d['date']}")
        continue
    try:
        svc.files().delete(fileId=d["file_id"]).execute()
        if i % 20 == 0:
            print(f"  [{i+1}/{len(deletes)}] OK {d['sid']} de {d['date']}")
    except Exception as e:
        errors.append({**d,"err":str(e)[:80]})
        print(f"  ❌ {d['sid']}: {e}")

print(f"\n{'='*60}\n=== RESUMEN ===")
print(f"Date folders: {len(date_folders)}")
print(f"Total label PDFs: {total_files}")
print(f"Shipment IDs únicos: {len(by_ship)}")
print(f"Shipment IDs duplicados: {len(dups)}")
print(f"Archivos eliminados: {0 if DRY_RUN else len(deletes)-len(errors)}")
print(f"Errores: {len(errors)}")

if TG and TGCID:
    import requests
    msg = f"🧹 *DEDUP Drive ETIQUETAS* {'(DRY RUN)' if DRY_RUN else ''}\n\n"
    msg += f"📁 Carpetas día: *{len(date_folders)}*\n"
    msg += f"📄 PDFs totales: *{total_files}*\n"
    msg += f"🔢 Envíos únicos: *{len(by_ship)}*\n"
    msg += f"⚠️ Envíos duplicados: *{len(dups)}*\n"
    if not DRY_RUN:
        msg += f"🗑️ Eliminados: *{len(deletes)-len(errors)}*\n"
        if errors: msg += f"❌ Errores: *{len(errors)}*\n"
    if dups:
        # mostrar distribución por fecha-fuente
        date_count = defaultdict(int)
        for d in deletes: date_count[d["date"]] += 1
        msg += f"\n*Borradas por fecha:*\n"
        for date in sorted(date_count.keys()):
            msg += f"• {date}: {date_count[date]}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
