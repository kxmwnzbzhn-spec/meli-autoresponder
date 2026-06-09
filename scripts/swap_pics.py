"""Upload 5 real perfume images to MELI + replace pictures on MLM2996221667."""
import os, glob, requests, json
API="https://api.mercadolibre.com"

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM="MLM2996221667"

# Upload all 5 PNGs in order
files=sorted(glob.glob("perf_imgs/*.png"))
print(f"Found {len(files)} local imgs: {files}")
picture_ids=[]
for fp in files:
    with open(fp,"rb") as f: data=f.read()
    print(f"  Uploading {fp} ({len(data)} bytes)...")
    files_form={"file":(os.path.basename(fp),data,"image/png")}
    rr=requests.post(f"{API}/pictures/items/upload",
        headers={"Authorization":f"Bearer {AT}"},files=files_form,timeout=30)
    if rr.status_code in (200,201):
        pid=rr.json().get("id")
        if pid: picture_ids.append(pid); print(f"    ✅ {pid}")
    else:
        print(f"    ❌ HTTP {rr.status_code}: {rr.text[:200]}")

print(f"\nUploaded {len(picture_ids)} pictures to MELI")

# PUT new pictures on the item
payload={"pictures":[{"id":pid} for pid in picture_ids]}
rp=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=payload,timeout=20)
print(f"\nPUT /items/{ITEM} pictures: HTTP {rp.status_code}: {rp.text[:500]}")

if rp.status_code in (200,201):
    g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
    print(f"\n[AFTER] {ITEM} status={g2.get('status')} qty={g2.get('available_quantity')}")
    print(f"  Pictures count: {len(g2.get('pictures') or [])}")
    print(f"  Permalink: {g2.get('permalink')}")
