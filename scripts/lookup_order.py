"""Buscar el ID en Asva exhaustivamente: como order, shipment, pack, partial last digits."""
import os, sys, requests, time
SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")
APP_SECRET = os.environ["MELI_APP_SECRET"]
TARGET = os.environ["TARGET_ID"]
LAST_DIGITS = TARGET[-7:]  # últimos 7 dígitos

def get_at(acc_u):
    r = requests.get(f"{SB_URL}/rest/v1/meli_tokens",
        params={"account":f"eq.{acc_u}","select":"refresh_token","limit":1},
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10).json()
    if not r: return None, None
    rt = r[0]["refresh_token"]
    tr = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
    new_rt = tr.get("refresh_token"); at = tr.get("access_token")
    err = tr.get("error")
    if new_rt and at:
        requests.patch(f"{SB_URL}/rest/v1/meli_tokens",
            params={"account":f"eq.{acc_u}"},
            json={"refresh_token":new_rt,"access_token":at},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"}, timeout=10)
    return at, err

print(f"=== Búsqueda exhaustiva ID {TARGET} (últimos 7: {LAST_DIGITS}) ===\n")

# 1) Asva - obtener UID + token fresco
at, err = get_at("ASVA")
print(f"[ASVA] token: {'OK' if at else 'FAIL ('+str(err)+')'}")
if not at: sys.exit(1)
H = {"Authorization": f"Bearer {at}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
print(f"[ASVA] uid={me.get('id')} nick={me.get('nickname')}")

# 2) Try as order
print(f"\n--- Como /orders/{TARGET} ---")
r = requests.get(f"https://api.mercadolibre.com/orders/{TARGET}", headers=H, timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:200]}")

# 3) Try as shipment
print(f"\n--- Como /shipments/{TARGET} ---")
r = requests.get(f"https://api.mercadolibre.com/shipments/{TARGET}", headers=H, timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:300]}")

# 4) Try as pack
print(f"\n--- Como /packs/{TARGET} ---")
r = requests.get(f"https://api.mercadolibre.com/packs/{TARGET}", headers=H, timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:300]}")

# 5) Search Asva orders for matching last digits
print(f"\n--- Buscar últimos 7 dígitos '{LAST_DIGITS}' en órdenes Asva ---")
found = []
uid = me.get('id')
for off in range(0, 600, 50):
    r = requests.get("https://api.mercadolibre.com/orders/search",
        params={"seller":uid,"sort":"date_desc","limit":50,"offset":off},
        headers=H, timeout=15).json()
    for o in r.get("results", []):
        oid = str(o.get('id',''))
        sid = str((o.get('shipping') or {}).get('id',''))
        if LAST_DIGITS in oid or LAST_DIGITS in sid:
            items = [it.get('item',{}).get('title','')[:60] for it in o.get('order_items',[])]
            found.append((oid, sid, o.get('status'), items))
    if not r.get("results"): break
    time.sleep(0.05)
if found:
    print(f"  ¡{len(found)} matches!:")
    for oid, sid, st, items in found:
        print(f"    order={oid} ship={sid} status={st} items={items}")
else:
    print(f"  ❌ Nada con últimos 7 dígitos '{LAST_DIGITS}' en últimas 600 órdenes Asva")
