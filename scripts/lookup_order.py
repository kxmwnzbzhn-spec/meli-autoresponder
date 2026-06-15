"""Diagnostic: busca un order_id en las 3 cuentas, reporta status del shipment."""
import os, sys, requests
SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]
TARGET = os.environ["TARGET_ID"]

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

ACCOUNTS = [("Claribel","CLARIBEL"),("Asva","ASVA"),("Adrian","AH")]
print(f"=== Buscando ID {TARGET} ===")
for disp, upper in ACCOUNTS:
    at = get_at(upper)
    if not at: print(f"[{disp}] token fail"); continue
    H = {"Authorization": f"Bearer {at}"}
    # Try as order
    r = requests.get(f"https://api.mercadolibre.com/orders/{TARGET}", headers=H, timeout=10)
    if r.status_code == 200:
        o = r.json()
        if o.get('id'):
            print(f"\n✅ ORDEN EN {disp.upper()}:")
            print(f"  order.status: {o.get('status')}")
            print(f"  date_created: {o.get('date_created')}")
            sid = (o.get('shipping') or {}).get('id')
            print(f"  shipping.id: {sid}")
            print(f"  items: {[it.get('item',{}).get('title','')[:60] for it in o.get('order_items',[])]}")
            if sid:
                rs = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10)
                if rs.status_code == 200:
                    s = rs.json()
                    print(f"\n  SHIPMENT {sid}:")
                    print(f"    status: {s.get('status')}")
                    print(f"    substatus: {s.get('substatus')}")
                    print(f"    logistic_type: {s.get('logistic_type')}")
                    print(f"    shipping_mode: {s.get('shipping_mode')}")
                    print(f"    handling_limit: {s.get('date_handling',{}).get('estimated_handling_limit',{}).get('date')}")
            break
    # Try as shipment
    rs = requests.get(f"https://api.mercadolibre.com/shipments/{TARGET}", headers=H, timeout=10)
    if rs.status_code == 200:
        s = rs.json()
        if s.get('id'):
            print(f"\n✅ SHIPMENT EN {disp.upper()}:")
            print(f"  status: {s.get('status')}")
            print(f"  substatus: {s.get('substatus')}")
            break
else:
    print("❌ No encontrado en ninguna cuenta")
