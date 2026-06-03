"""Toma artifact PDFs de 3 runs labels_one, los combina y sube a Drive en subcarpeta del día."""
import os, sys, requests, zipfile, io, json
from datetime import datetime, timezone, timedelta
from pypdf import PdfReader, PdfWriter

TZ = timezone(timedelta(hours=-6))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")
REPO = "kxmwnzbzhn-spec/meli-autoresponder"
RUN_IDS = os.environ["RUN_IDS"].split(",")  # ej "26884653934,26884655371,26884657022"
LABELS = os.environ.get("LABELS", ",".join(["Cuenta"+str(i+1) for i in range(len(RUN_IDS))])).split(",")
DRIVE_FOLDER = os.environ.get("DRIVE_FOLDER_ID", "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL")
GH_TOKEN = os.environ["GH_TOKEN_FOR_API"]

H = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}
writer = PdfWriter()
summary = []
for rid, label in zip(RUN_IDS, LABELS):
    arts = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs/{rid}/artifacts", headers=H).json()
    if not arts.get("artifacts"):
        print(f"  ! {label} ({rid}): no artifacts")
        continue
    url = arts["artifacts"][0]["archive_download_url"]
    r = requests.get(url, headers=H, allow_redirects=True)
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    pdf_name = [n for n in zf.namelist() if n.endswith(".pdf")][0]
    pdf_bytes = zf.read(pdf_name)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    for p in reader.pages: writer.add_page(p)
    print(f"  + {label}: {len(reader.pages)} págs")
    summary.append(f"{label}:{len(reader.pages)}")

out_name = f"ETIQUETAS_{TODAY}_combo.pdf"
with open(out_name, "wb") as f: writer.write(f)
print(f"\nTotal: {len(writer.pages)} págs → {out_name}")

# Drive upload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
                    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
                    scopes=["https://www.googleapis.com/auth/drive"])
creds.refresh(GRequest())
svc = build("drive","v3",credentials=creds,cache_discovery=False)

# Find/create today's subfolder
q = f"name='{TODAY}' and mimeType='application/vnd.google-apps.folder' and '{DRIVE_FOLDER}' in parents and trashed=false"
res = svc.files().list(q=q, fields="files(id,name)").execute()
files = res.get("files", [])
if files:
    day_id = files[0]["id"]
    print(f"Subcarpeta {TODAY} existe: {day_id}")
else:
    f = svc.files().create(body={"name":TODAY,"mimeType":"application/vnd.google-apps.folder","parents":[DRIVE_FOLDER]},
                           fields="id,webViewLink").execute()
    day_id = f["id"]
    print(f"Subcarpeta {TODAY} creada: {day_id}")

# Upload
media = MediaFileUpload(out_name, mimetype="application/pdf", resumable=True, chunksize=1024*1024)
req = svc.files().create(body={"name":out_name,"parents":[day_id]}, media_body=media,
                         fields="id,name,webViewLink")
resp = None
while resp is None: _, resp = req.next_chunk(num_retries=3)
print(f"\n✅ Subido: {resp.get('name')} → {resp.get('webViewLink')}")
print(f"📂 Carpeta del día: https://drive.google.com/drive/folders/{day_id}")

# Telegram
TG = os.environ.get("TG_TOKEN",""); TGC = os.environ.get("TG_CHAT","")
if TG and TGC:
    text = (f"🤖 <b>Etiquetas combo manual {TODAY}</b>\n"
            f"📊 {len(writer.pages)} págs ({' · '.join(summary)})\n"
            f"📂 <a href=\"https://drive.google.com/drive/folders/{day_id}\">Carpeta</a>\n"
            f"📄 <a href=\"{resp.get('webViewLink')}\">PDF</a>")
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id":TGC,"text":text,"parse_mode":"HTML","disable_web_page_preview":"true"}, timeout=10)
