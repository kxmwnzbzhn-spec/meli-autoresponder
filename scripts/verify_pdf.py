import os, io, json, re
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

FILE_ID = os.environ["FILE_ID"]
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"], scopes=SCOPES)
creds.refresh(Request())
svc = build("drive","v3",credentials=creds,cache_discovery=False)

meta = svc.files().get(fileId=FILE_ID, fields="id,name,size,mimeType,webViewLink,parents",
    supportsAllDrives=True).execute()
print(f"[meta] name={meta['name']} size={int(meta['size'])/1024:.1f}KB link={meta.get('webViewLink')}")

req = svc.files().get_media(fileId=FILE_ID, supportsAllDrives=True)
buf = io.BytesIO(); dl = MediaIoBaseDownload(buf, req)
done = False
while not done:
    _, done = dl.next_chunk()
buf.seek(0)
pdf = PdfReader(buf)
n_pages = len(pdf.pages)
print(f"[pdf] pages={n_pages}")

ships_by_page = []
missing = []
for i,p in enumerate(pdf.pages):
    t = p.extract_text() or ""
    m = re.search(r"Ship:\s*(\d+)", t)
    if m:
        ships_by_page.append(m.group(1))
    else:
        missing.append(i+1)
        ships_by_page.append(None)

valid = [s for s in ships_by_page if s]
uniq = sorted(set(valid))
dupes = {}
for s in valid:
    dupes[s] = dupes.get(s,0)+1
dup_list = [s for s,c in dupes.items() if c>1]

print(f"[ship] total_ship_lines={len(valid)} unique={len(uniq)} pages_without_Ship={len(missing)}")
print(f"[ship] duplicates_count={len(dup_list)}")
if dup_list:
    print(f"[ship] duplicated_ids={dup_list[:20]}")
if missing:
    print(f"[ship] pages_missing_Ship={missing[:20]}")

# expected counts per account
report = {
  "file_id": FILE_ID,
  "name": meta['name'],
  "size_kb": round(int(meta['size'])/1024,1),
  "link": meta.get('webViewLink'),
  "pages": n_pages,
  "unique_ships": len(uniq),
  "duplicate_ships": len(dup_list),
  "pages_missing_Ship": len(missing),
}
print("REPORT=" + json.dumps(report, indent=2))
