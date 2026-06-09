"""Activate item + register priority replenish (qty=1 c/30s)."""
import os, requests
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM="MLM3849137034"
USER_MSG="activa en asva la publicacion 3849137034 solo pon 1 a la vista en stock y activas el restock cada 30 segundos"

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} qty={g.get('available_quantity')} title={(g.get('title') or '')[:80]}")

# 1) Activate with qty=1
rr=requests.put(f"{API}/items/{ITEM}",headers=HJ,
    json={"status":"active","available_quantity":1},timeout=15)
print(f"[ACTIVATE qty=1] HTTP {rr.status_code}: {rr.text[:300]}")

# 2) Remove from no_replenish (was added when paused earlier)
requests.delete(f"{SBU}/rest/v1/meli_no_replenish_items?item_id=eq.{ITEM}",headers=SBH,timeout=10)
print("[no_replenish] removed if existed")

# 3) Upsert into priority_replenish (default_qty=1)
rpr=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
    json={"item_id":ITEM,"account":"ASVA","default_qty":1,
          "product_name":g.get("title","")[:200]},timeout=10)
print(f"[priority_replenish UPSERT] HTTP {rpr.status_code}")

# 4) Directive
requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"ASVA","scope":"item","scope_value":ITEM,
          "directive_type":"priority_replenish","value_numeric":1,
          "raw_user_message":USER_MSG},timeout=10)
print("[DIRECTIVE registered]")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"\n[AFTER] status={g2.get('status')} qty={g2.get('available_quantity')}")
print(f"Permalink: {g2.get('permalink')}")
