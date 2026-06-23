"""Toma lista de pack_ids, resuelve cada uno a shipment_id por cuenta, descarga labels, combina."""
import os, sys, io, requests, time
from pypdf import PdfReader, PdfWriter

SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]
PACK_IDS = [s.strip() for s in os.environ["PACK_IDS"].split(",") if s.strip()]

ACCOUNTS = ["CLARIBEL","ASVA","AH","WILBERT","JUAN","BREN","RAYMUNDO","RMAYCHI","YC_NEW"]

def get_at(acc_u):
    r = requests.get(f"{SB_URL}/rest/v1/meli_tokens",
        params={"account":f"eq.{acc_u}","select":"refresh_token","limit":1},
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10).json()
    if not r: return None
    rt = r[0]["refresh_token"]
    tr = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
    new_rt = tr.get("refresh_token"); at = tr.get("access_token")
    if new_rt and at:
        requests.patch(f"{SB_URL}/rest/v1/meli_tokens",
            params={"account":f"eq.{acc_u}"},
            json={"refresh_token":new_rt,"access_token":at},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"}, timeout=10)
    return at

# Refresh tokens for all
TOKENS = {}
for acc in ACCOUNTS:
    at = get_at(acc)
    if at: TOKENS[acc] = at
    print(f"  [{acc}] token: {'OK' if at else 'FAIL'}")

# Resolve each pack to (account, shipment_id)
resolved = []
for pid in PACK_IDS:
    found = False
    for acc, at in TOKENS.items():
        r = requests.get(f"https://api.mercadolibre.com/packs/{pid}",
            headers={"Authorization":f"Bearer {at}"}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            sid = (d.get("shipment") or {}).get("id")
            if sid:
                # Get items
                title = "?"
                orders = d.get("orders", [])
                if orders:
                    oid = orders[0].get("id")
                    ro = requests.get(f"https://api.mercadolibre.com/orders/{oid}",
                        headers={"Authorization":f"Bearer {at}"}, timeout=10)
                    if ro.status_code == 200:
                        od = ro.json()
                        items = od.get("order_items",[])
                        if items: title = items[0].get("item",{}).get("title","")[:80]
                resolved.append((pid, acc, sid, title))
                print(f"  pack {pid} → [{acc}] ship {sid} · {title}")
                found = True
                break
    if not found:
        print(f"  ❌ pack {pid} no encontrado en ninguna cuenta")
        resolved.append((pid, None, None, None))

# Download labels
writer = PdfWriter()
ok = 0
for pid, acc, sid, title in resolved:
    if not sid: continue
    at = TOKENS[acc]
    r = requests.get("https://api.mercadolibre.com/shipment_labels",
        headers={"Authorization":f"Bearer {at}"},
        params={"shipment_ids":sid,"response_type":"pdf","savePdf":"Y"}, timeout=30)
    if r.status_code == 200 and r.headers.get("content-type","").lower().startswith("application/pdf"):
        lp = PdfReader(io.BytesIO(r.content))
        for p in lp.pages: writer.add_page(p)
        ok += 1
    else:
        print(f"  ❌ ship {sid} HTTP {r.status_code}")

with open("ETIQUETAS_PACKS.pdf","wb") as f: writer.write(f)
print(f"\n✅ {ok}/{len(resolved)} labels en ETIQUETAS_PACKS.pdf · {len(writer.pages)} págs")
