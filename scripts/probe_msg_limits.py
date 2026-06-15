import os, requests, json, time, base64
from datetime import datetime, timezone, timedelta
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
ITEM_TARGET="MLM2976325463"
SELLER=3417664339

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}

# Get a few orders and check what message intents are ALLOWED per pack
print("\n=== Sample 5 orders + check message constraints ===")
r=requests.get(f"{API}/orders/search",headers=H,
  params={"seller":SELLER,"item":ITEM_TARGET,"sort":"date_desc","limit":15},timeout=15)
results=r.json().get("results",[])

for o in results[:8]:
  oid=o.get("id")
  pid=str(o.get("pack_id") or oid)
  status=o.get("status"); date_closed=o.get("date_closed")
  buyer=(o.get("buyer") or {}).get("id")
  ship=(o.get("shipping") or {})
  ship_id=ship.get("id")
  print(f"\n--- order={oid} pack={pid} status={status} closed={date_closed} buyer={buyer} ship={ship_id} ---")
  
  # Get shipment status
  if ship_id:
    s=requests.get(f"{API}/shipments/{ship_id}",headers=H,timeout=10).json()
    print(f"  shipment status={s.get('status')} sub={s.get('substatus')} delivered_at={s.get('status_history',{}).get('date_delivered') or s.get('date_delivered')}")
  
  # Check what message intents are allowed for this pack
  caps=requests.get(f"{API}/messages/packs/{pid}/sellers/{SELLER}/option",headers=H,timeout=10)
  print(f"  [msg options] HTTP {caps.status_code}: {caps.text[:500]}")
  
  # Also try /caps
  c2=requests.get(f"{API}/messages/caps?packId={pid}&userRole=seller",headers=H,timeout=10)
  print(f"  [caps] HTTP {c2.status_code}: {c2.text[:400]}")

# Check predefined templates / intents
print("\n=== Buscar endpoints templates ===")
for url in [
  f"{API}/messages/templates?role=seller",
  f"{API}/messages/templates",
  f"{API}/post-purchase/v1/orders/template-messages",
]:
  r=requests.get(url,headers=H,timeout=10)
  print(f"{url} -> HTTP {r.status_code}: {r.text[:300]}")
