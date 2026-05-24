import os, requests
import meli_token
IIDS = ["MLM2950801633", "MLM2950801613", "MLM2950827387"]
EXP = 3364413125  # Yiriam
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
AT = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {AT}"}; HJ = {**H, "Content-Type": "application/json"}
for IID in IIDS:
    it = requests.get(f"{API}/items/{IID}?attributes=id,seller_id,status,title", headers=H, timeout=20).json()
    print(f"\n{IID}: seller={it.get('seller_id')} status={it.get('status')} '{(it.get('title') or '')[:40]}'")
    if it.get("seller_id") != EXP:
        print("  SKIP (no Yiriam)"); continue
    if it.get("status") == "active":
        print("  pause:", requests.put(f"{API}/items/{IID}", headers=HJ, json={"status":"paused"}, timeout=20).status_code)
    print("  close:", requests.put(f"{API}/items/{IID}", headers=HJ, json={"status":"closed"}, timeout=20).status_code)
    print("  delete:", requests.put(f"{API}/items/{IID}", headers=HJ, json={"deleted":"true"}, timeout=20).status_code)
print("\nDONE")
