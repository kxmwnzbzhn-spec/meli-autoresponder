"""Pull last 30 días de orders por cuenta, upsert a recent_shipments en Supabase.
Sirve para que el buscador encuentre envíos delivered/cancelled cuando no estén en manifest."""
import os, sys, requests, time, json
from datetime import datetime, timezone, timedelta

SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("Claribel","CLARIBEL"),
    ("Asva","ASVA"),
    ("Adrian","AH"),
]

def get_at(account_upper):
    """Lee refresh, refresca, regresa access_token + actualiza Supabase."""
    r = requests.get(f"{SB_URL}/rest/v1/meli_tokens",
        params={"account":f"eq.{account_upper}","select":"refresh_token","limit":1},
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10).json()
    if not r: return None
    rt = r[0]["refresh_token"]
    tr = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
    new_rt = tr.get("refresh_token"); at = tr.get("access_token")
    if new_rt:
        requests.patch(f"{SB_URL}/rest/v1/meli_tokens",
            params={"account":f"eq.{account_upper}"},
            json={"refresh_token":new_rt,"access_token":at},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"}, timeout=10)
    return at

def upsert_batch(recs):
    if not recs: return
    for i in range(0, len(recs), 500):
        chunk = recs[i:i+500]
        r = requests.post(f"{SB_URL}/rest/v1/recent_shipments",
            json=chunk,
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json",
                     "Prefer":"resolution=merge-duplicates,return=minimal"}, timeout=30)
        if r.status_code not in (200,201,204):
            print(f"  upsert HTTP {r.status_code}: {r.text[:200]}")

def get_uid(at):
    return requests.get("https://api.mercadolibre.com/users/me",
        headers={"Authorization":f"Bearer {at}"}, timeout=10).json().get("id")

def dump_account(display, upper):
    print(f"\n=== {display} ===", flush=True)
    at = get_at(upper)
    if not at: print("  token fail"); return 0
    uid = get_uid(at)
    H = {"Authorization": f"Bearer {at}"}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    # Pull paid orders sorted by date_desc
    all_records = {}
    off = 0
    while off < 2500:  # cap at 2500 = ~30 días para Asva
        r = requests.get("https://api.mercadolibre.com/orders/search",
            params={"seller":uid,"sort":"date_desc","limit":50,"offset":off},
            headers=H, timeout=20).json()
        results = r.get("results", [])
        if not results: break
        oldest_in_batch = None
        for o in results:
            sid_v = (o.get("shipping") or {}).get("id")
            if not sid_v: continue
            date_created = o.get("date_created")
            oldest_in_batch = date_created
            if date_created < cutoff: continue
            items = o.get("order_items",[])
            title = items[0].get("item",{}).get("title","")[:200] if items else ""
            buyer = (o.get("buyer") or {}).get("nickname","")
            # NO llamamos /shipments/sid aquí — sería 2500 calls. Confiamos en status del order.
            all_records[str(sid_v)] = {
                "sid": str(sid_v),
                "account": display,
                "status": o.get("status"),
                "substatus": None,  # se actualiza para los pendientes via otro mecanismo
                "product_title": title,
                "buyer": buyer,
                "date_created": date_created,
                "last_updated": o.get("last_updated"),
                "refreshed_at": datetime.now(timezone.utc).isoformat(),
            }
        # break si ya fuimos más allá del cutoff
        if oldest_in_batch and oldest_in_batch < cutoff: break
        off += 50
        time.sleep(0.05)
    print(f"  pulled {len(all_records)} orders en últimos 30 días")
    # Ahora para los que tienen substatus pending, llamar /shipments/sid para enriquecer
    pending = [r for r in all_records.values() if r["status"] == "paid"][:100]  # cap
    for rec in pending:
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{rec['sid']}", headers=H, timeout=8).json()
            rec["substatus"] = sh.get("substatus")
            # Para los delivered, obtener delivered_at
            for evt in (sh.get("status_history") or {}).get("date_delivered", []):
                rec["delivered_at"] = evt
                break
        except: pass
    upsert_batch(list(all_records.values()))
    print(f"  upserted {len(all_records)}")
    return len(all_records)

def main():
    total = 0
    for display, upper in ACCOUNTS:
        total += dump_account(display, upper)
    print(f"\n✅ TOTAL: {total} shipments en recent_shipments")

if __name__ == "__main__":
    main()
