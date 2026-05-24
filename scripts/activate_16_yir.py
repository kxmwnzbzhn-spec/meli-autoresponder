import os, requests
import meli_token

IDS = ["MLM5291774150","MLM5291785036","MLM5363034838","MLM2940662359","MLM2940047221",
       "MLM2950827385","MLM2909183147","MLM5390372034","MLM2950790163","MLM2950801625",
       "MLM5364336572","MLM2950827397","MLM2950827407","MLM5390371996","MLM2950790175",
       "MLM2950801553"]
EXPECTED_SELLER = 3364413125  # Yiriam / YC_NEW

RT = os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
AT = meli_token.refresh(RT).json()["access_token"]
H  = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}

ok = 0; skipped = 0; errs = 0
for iid in IDS:
    it = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,seller_id,status,available_quantity,title", headers=H, timeout=20).json()
    if it.get("seller_id") != EXPECTED_SELLER:
        print(f"  SKIP {iid}: seller={it.get('seller_id')} (no es Yiriam) / {it.get('status')}")
        skipped += 1; continue
    cur_status = it.get("status"); cur_qty = it.get("available_quantity", 0) or 0
    body = {"status": "active"}
    if cur_qty < 1:
        body["available_quantity"] = 1
    if cur_status == "active" and cur_qty >= 1:
        print(f"  YA ACTIVO {iid} qty={cur_qty} '{it.get('title','')[:40]}'")
        ok += 1; continue
    r = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=HJ, json=body, timeout=20)
    fin = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,available_quantity", headers=H, timeout=20).json()
    tag = "OK" if r.status_code == 200 and fin.get("status") == "active" else f"ERR({r.status_code})"
    if tag == "OK": ok += 1
    else: errs += 1
    print(f"  {tag} {iid}: {cur_status}/{cur_qty} -> {fin.get('status')}/{fin.get('available_quantity')} {('' if r.status_code==200 else r.text[:150])}")

print(f"\nRESUMEN activacion: ACTIVOS={ok}  SKIP={skipped}  ERR={errs}  total={len(IDS)}")
print("DONE")
