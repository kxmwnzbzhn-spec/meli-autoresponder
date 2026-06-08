"""Marca como 'printed' en MELI los SIDs del manifest (savePdf=Y).
Limpieza one-shot para SIDs cuyo label se descargó sin savePdf=Y."""
import os, sys, requests, time
SB_URL = os.environ["SUPABASE_URL"].rstrip('/')
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]

def get_token(account_upper):
    r = requests.get(f"{SB_URL}/rest/v1/meli_tokens",
        params={"account":f"eq.{account_upper}","select":"refresh_token","limit":1},
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10).json()
    rt = r[0]["refresh_token"] if r else None
    if not rt: return None
    tr = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,
        "refresh_token":rt}, timeout=15).json()
    new_rt = tr.get("refresh_token"); at = tr.get("access_token")
    if new_rt:
        requests.patch(f"{SB_URL}/rest/v1/meli_tokens",
            params={"account":f"eq.{account_upper}"},
            json={"refresh_token":new_rt,"access_token":at},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"}, timeout=10)
    return at

# Get manifest to map SID -> account
manifest = requests.get("https://raw.githubusercontent.com/kxmwnzbzhn-spec/meli-autoresponder/main/data/manifest.json", timeout=20).json()
sid_to_account = {s["sid_str"]: s["account"] for s in manifest.get("shipments", [])}
print(f"Manifest tiene {len(sid_to_account)} SIDs")

# Read SIDs to mark
SIDS = [s.strip() for s in os.environ["SIDS"].split(",") if s.strip()]
print(f"SIDs a marcar: {len(SIDS)}")

# Group by account
tokens = {}
by_account = {}
for sid in SIDS:
    acc = sid_to_account.get(sid)
    if not acc:
        print(f"  ! {sid}: no en manifest, skip"); continue
    by_account.setdefault(acc, []).append(sid)

# Account display name → uppercase for Supabase lookup
acc_upper = {"Claribel":"CLARIBEL","Asva":"ASVA","Adrian":"AH","Yiriam":"YC_NEW"}

total_marked = 0; total_failed = 0
for acc, sids in by_account.items():
    acc_u = acc_upper.get(acc, acc.upper())
    print(f"\n=== {acc} ({acc_u}): {len(sids)} SIDs ===")
    at = get_token(acc_u)
    if not at: print(f"  ❌ token fail"); continue
    H = {"Authorization": f"Bearer {at}"}
    for i, sid in enumerate(sids):
        r = requests.get("https://api.mercadolibre.com/shipment_labels", headers=H,
            params={"shipment_ids":sid,"response_type":"pdf","savePdf":"Y"}, timeout=20)
        if r.status_code == 200:
            total_marked += 1
        else:
            total_failed += 1
            print(f"  ! {sid}: HTTP {r.status_code}")
        if (i+1) % 25 == 0: print(f"  ...{i+1}/{len(sids)}")
        time.sleep(0.06)

print(f"\n✅ Marcados: {total_marked} | ❌ Fail: {total_failed}")
