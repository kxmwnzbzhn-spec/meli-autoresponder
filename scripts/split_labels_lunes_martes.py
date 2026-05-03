#!/usr/bin/env python3
"""SPLIT etiquetas: separa shipments en 2 grupos por deadline y los sube a Drive
en carpetas distintas para identificar prioridad.

Grupo 1 — "LUNES_4_MAYO":   shipments con deadline <= 2026-05-04 (incluye OVERDUE)
Grupo 2 — "MARTES_5_MAYO":  shipments con deadline >= 2026-05-05

Para cada grupo:
- Descarga las etiquetas individuales de MELI shipment_labels API
- Merge en un solo PDF
- Sube a Drive ETIQUETAS/<grupo>/
"""
import os, io, json, re, sys, time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import requests
from pypdf import PdfReader, PdfWriter
from google.oauth2.credentials import Credentials as UC
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID = os.environ.get("TELEGRAM_CHAT_ID","")

ACCS = {
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
}

TZ_CDMX = timezone(timedelta(hours=-6))
LUNES = datetime.fromisoformat("2026-05-04").replace(hour=23, minute=59, tzinfo=TZ_CDMX)
print(f"Cutoff lunes: {LUNES.isoformat()}")

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")


# ====== FASE 1: clasificar shipments en lunes/martes ======
NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=10)
lunes_by_acc = defaultdict(list)
martes_by_acc = defaultdict(list)

for acc, rt in ACCS.items():
    if not rt: continue
    print(f"\n=== {acc} ===")
    at = tok(rt)
    if not at: continue
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me.get("id")
    if not uid: continue

    orders = []
    offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search",
            headers=H, timeout=20,
            params={"seller":uid, "order.status":"paid",
                    "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":offset}).json()
        res = r.get("results",[])
        if not res: break
        orders.extend(res)
        offset += len(res)
        if offset >= r.get("paging",{}).get("total",0): break

    ship_ids = set()
    for o in orders:
        s = (o.get("shipping") or {}).get("id")
        if s: ship_ids.add(s)
    print(f"  shipments: {len(ship_ids)}")

    for sid in ship_ids:
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}",
                              headers=H, timeout=10).json()
            status = sh.get("status")
            substatus = sh.get("substatus")
            if status not in ("ready_to_ship","handling"): continue
            if substatus in ("shipped","ready_to_pickup"): continue

            # SLA endpoint
            deadline = None
            try:
                sla = requests.get(f"https://api.mercadolibre.com/shipments/{sid}/sla",
                                   headers=H, timeout=8).json()
                ed = sla.get("expected_date")
                if ed:
                    deadline = datetime.fromisoformat(ed.replace("Z","+00:00")).astimezone(TZ_CDMX)
            except Exception: pass

            if not deadline:
                hist = sh.get("status_history") or {}
                dh = hist.get("date_handling")
                if dh:
                    dh_dt = datetime.fromisoformat(dh.replace("Z","+00:00"))
                    deadline = (dh_dt + timedelta(hours=48)).astimezone(TZ_CDMX)

            if not deadline: continue

            entry = {"sid":sid, "deadline":deadline, "token":at}
            if deadline <= LUNES:
                lunes_by_acc[acc].append(entry)
            else:
                martes_by_acc[acc].append(entry)
            time.sleep(0.04)
        except Exception as e:
            print(f"  err {sid}: {str(e)[:60]}")

total_lunes = sum(len(v) for v in lunes_by_acc.values())
total_martes = sum(len(v) for v in martes_by_acc.values())
print(f"\n=== Clasificación ===")
print(f"LUNES: {total_lunes}")
print(f"MARTES o despues: {total_martes}")
for acc in ACCS:
    print(f"  {acc}: lunes={len(lunes_by_acc[acc])} martes={len(martes_by_acc[acc])}")


# ====== FASE 2: descargar etiquetas y mergear PDFs ======
def fetch_labels_pdf(token, sids, out_path):
    """Descarga etiquetas en PDF. MELI permite ~10 ids por request."""
    H = {"Authorization": f"Bearer {token}"}
    writer = PdfWriter()
    failed = []
    BATCH = 10
    for i in range(0, len(sids), BATCH):
        chunk = sids[i:i+BATCH]
        url = "https://api.mercadolibre.com/shipment_labels"
        params = {"shipment_ids":",".join(map(str,chunk)), "response_type":"pdf"}
        try:
            r = requests.get(url, headers=H, params=params, timeout=60)
            if r.status_code == 200 and r.headers.get("content-type","").lower().startswith("application/pdf"):
                pdf = PdfReader(io.BytesIO(r.content))
                for page in pdf.pages:
                    writer.add_page(page)
                print(f"  + {len(chunk)} etiquetas (batch {i//BATCH+1})")
            else:
                print(f"  ❌ batch {i//BATCH+1}: {r.status_code} {r.text[:100]}")
                failed.extend(chunk)
        except Exception as e:
            print(f"  ! err: {e}")
            failed.extend(chunk)
        time.sleep(0.3)
    if writer.pages:
        with open(out_path, "wb") as f:
            writer.write(f)
        print(f"  ✅ {len(writer.pages)} pages → {out_path}")
        return len(writer.pages), failed
    return 0, failed


pdfs_to_upload = []  # [(group_name, file_path)]

for group_name, by_acc in [("LUNES_4_MAYO", lunes_by_acc), ("MARTES_5_MAYO_o_despues", martes_by_acc)]:
    print(f"\n=== Generando PDF {group_name} ===")
    # Por cuenta: necesitamos un token diferente
    for acc, entries in by_acc.items():
        if not entries: continue
        token = entries[0]["token"]
        sids = [e["sid"] for e in entries]
        out = f"{group_name}__{acc}.pdf"
        n, failed = fetch_labels_pdf(token, sids, out)
        if n > 0:
            pdfs_to_upload.append((group_name, out, n, acc))


# ====== FASE 3: subir a Drive en carpetas separadas ======
SCOPES = ["https://www.googleapis.com/auth/drive"]
oauth_creds = UC(token=None,
    refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
    scopes=SCOPES)
svc = build("drive","v3",credentials=oauth_creds,cache_discovery=False)


def find_or_create(name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent: q += f" and '{parent}' in parents"
    r = svc.files().list(q=q, fields="files(id,name)").execute().get("files",[])
    if r: return r[0]["id"]
    body = {"name":name, "mimeType":"application/vnd.google-apps.folder"}
    if parent: body["parents"]=[parent]
    return svc.files().create(body=body, fields="id").execute()["id"]


parent_id = find_or_create("ETIQUETAS")
folders = {}
for grp in ["LUNES_4_MAYO", "MARTES_5_MAYO_o_despues"]:
    folders[grp] = find_or_create(grp, parent_id)
    print(f"📁 {grp} → {folders[grp]}")

uploads = 0
for group_name, fp, n, acc in pdfs_to_upload:
    media = MediaFileUpload(fp, mimetype="application/pdf", resumable=True)
    body = {"name": os.path.basename(fp), "parents": [folders[group_name]]}
    f = svc.files().create(body=body, media_body=media, fields="id,name").execute()
    print(f"  ✅ {group_name}/{f['name']} ({n} etiquetas) [{acc}]")
    uploads += 1

# Telegram
if TG and TGCID:
    msg = f"📦 *Etiquetas separadas en Drive*\n\n"
    msg += f"📁 *LUNES_4_MAYO*: {total_lunes} envíos\n"
    for acc, entries in lunes_by_acc.items():
        if entries: msg += f"  • {acc}: {len(entries)}\n"
    msg += f"\n📁 *MARTES_5_MAYO_o_despues*: {total_martes} envíos\n"
    for acc, entries in martes_by_acc.items():
        if entries: msg += f"  • {acc}: {len(entries)}\n"
    msg += f"\nDrive/ETIQUETAS/LUNES_4_MAYO/\nDrive/ETIQUETAS/MARTES_5_MAYO_o_despues/"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)

print(f"\n✅ {uploads} PDFs subidos")
