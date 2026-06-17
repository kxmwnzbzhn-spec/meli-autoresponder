"""Mira qué son MLM5525982716 y MLM5525381774."""
import os, requests
SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]

def get_at(acc_u):
    r = requests.get(f"{SB_URL}/rest/v1/meli_tokens",
        params={"account":f"eq.{acc_u}","select":"refresh_token","limit":1},
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10).json()
    if not r: return None
    rt = r[0]["refresh_token"]
    tr = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
    new_rt = tr.get("refresh_token"); at = tr.get("access_token")
    if new_rt:
        requests.patch(f"{SB_URL}/rest/v1/meli_tokens",
            params={"account":f"eq.{acc_u}"},
            json={"refresh_token":new_rt,"access_token":at},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"}, timeout=10)
    return at

# Try each account to find these items
ACCOUNTS = ["CLARIBEL","ASVA","AH","WILBERT","JUAN","BREN","RAYMUNDO","RMAYCHI","YC_NEW"]
items_to_find = ["MLM5525982716","MLM5525381774"]

for item_id in items_to_find:
    print(f"\n=== {item_id} ===")
    # Public endpoint first (no auth needed sometimes)
    r = requests.get(f"https://api.mercadolibre.com/items/{item_id}", timeout=10)
    if r.status_code == 200:
        d = r.json()
        print(f"  title: {d.get('title','')}")
        print(f"  seller_id: {d.get('seller_id')}")
        print(f"  condition: {d.get('condition')}")
        print(f"  price: {d.get('price')}")
    else:
        print(f"  HTTP {r.status_code} público — probando con token de cada cuenta")
        for acc in ACCOUNTS:
            at = get_at(acc)
            if not at: continue
            r = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers={"Authorization":f"Bearer {at}"}, timeout=10)
            if r.status_code == 200:
                d = r.json()
                print(f"  [{acc}] title: {d.get('title','')[:80]}")
                print(f"  [{acc}] seller_id: {d.get('seller_id')}")
                print(f"  [{acc}] condition: {d.get('condition')}")
                break
