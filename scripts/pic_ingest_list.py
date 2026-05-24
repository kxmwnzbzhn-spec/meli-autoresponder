import os, requests
import meli_token

# (orden, etiqueta, drive_file_id) — sensoriales de Flor de Nopal
FILES = [
    ("flor_de_nopal_espiritu", "12CzE_mx0gs9SCzfX3Jdd4ck2OgHZoK_u"),
    ("flor_de_nopal_ofrenda",  "1_bxd252JIT6Tz05dMltuCii9hU_j4v7I"),
    ("flor_de_nopal_ritual",   "18nUzU-MOuCxFseI5SW4ejSJEpj47Pu24"),
]
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

s = requests.Session()
def dl(fid):
    for u in (f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
              f"https://drive.google.com/uc?export=download&id={fid}&confirm=t",
              f"https://lh3.googleusercontent.com/d/{fid}=s2048"):
        try:
            r = s.get(u, headers=UA, timeout=90)
        except Exception as e:
            print(f"    dl EXC {e}"); continue
        b = r.content; m = b[:8]
        is_img = m.startswith(b"\x89PNG") or m.startswith(b"\xff\xd8\xff")
        print(f"    {u[:55]}... http={r.status_code} bytes={len(b)} img={is_img}")
        if r.status_code == 200 and is_img and len(b) > 5000:
            return b, ("png" if m.startswith(b"\x89PNG") else "jpg")
    return None, None

results = []
for label, fid in FILES:
    print(f"\n=== {label} ({fid}) ===")
    img, ext = dl(fid)
    if not img:
        print("  ❌ no descargable"); continue
    ctype = "image/png" if ext == "png" else "image/jpeg"
    rp = requests.post(f"{API}/pictures/items/upload", headers=H,
                       files={"file": (f"{label}.{ext}", img, ctype)}, timeout=120)
    print(f"  upload http={rp.status_code}")
    if rp.status_code < 300:
        pid = rp.json().get("id")
        results.append((label, pid)); print(f"  PICTURE_ID={pid}")
    else:
        print(f"  body={rp.text[:200]}")

print("\n=== RESUMEN ===")
for label, pid in results:
    print(f"  {label} -> {pid}")
print(f"subidas: {len(results)}/{len(FILES)}")
print("DONE")
