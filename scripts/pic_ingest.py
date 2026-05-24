import os, requests
import meli_token

# Fotos a ingerir: etiqueta -> Google Drive file id
DRIVE_FILES = {
    "principal_blanco": "1qBCiQrq1TNpfB6fOXxOWdRRnC-fQtM8M",
}
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}

def drive_download(fid):
    urls = [
        f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
        f"https://drive.google.com/uc?export=download&id={fid}&confirm=t",
        f"https://lh3.googleusercontent.com/d/{fid}=s2048",
    ]
    s = requests.Session()
    for u in urls:
        try:
            r = s.get(u, timeout=60, allow_redirects=True)
        except Exception as e:
            print(f"    dl EXC {u[:60]}: {e}"); continue
        ct = r.headers.get("Content-Type", "")
        body = r.content
        magic = body[:8]
        is_img = magic.startswith(b"\x89PNG") or magic.startswith(b"\xff\xd8\xff") or magic[:4] in (b"RIFF",)
        print(f"    try {u[:55]}... http={r.status_code} ct={ct[:30]} bytes={len(body)} img={is_img}")
        if r.status_code == 200 and is_img and len(body) > 5000:
            ext = "png" if magic.startswith(b"\x89PNG") else "jpg"
            return body, ext
    return None, None

for label, fid in DRIVE_FILES.items():
    print(f"\n=== {label} ({fid}) ===")
    img, ext = drive_download(fid)
    if not img:
        print("  ❌ no pude descargar (¿sigue privado?)"); continue
    ctype = "image/png" if ext == "png" else "image/jpeg"
    rp = requests.post(f"{API}/pictures/items/upload", headers=H,
                       files={"file": (f"{label}.{ext}", img, ctype)}, timeout=90)
    print(f"  upload http={rp.status_code}")
    if rp.status_code < 300:
        j = rp.json()
        vts = j.get("variations") or []
        maxv = max(((v.get("size") or "") for v in vts), default="")
        print(f"  PICTURE_ID={j.get('id')}  variations={len(vts)} max_size={maxv}")
    else:
        print(f"  body={rp.text[:300]}")
print("\nDONE")
