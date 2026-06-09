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

ITEM="MLM2886030837"
USER_MSG="activa esta en asva y no la pauses dejala que se acabe el stock de full 2886030837"

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] status={g.get('status')} qty={g.get('available_quantity')} inv={g.get('inventory_id')} title={(g.get('title') or '')[:80]}")

# Activate without changing qty
rr=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"status":"active"},timeout=15)
print(f"[ACTIVATE] HTTP {rr.status_code}: {rr.text[:300]}")

# Remove from priority_replenish + ADD to no_replenish (bot won't reactivate when Full stock depletes)
requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{ITEM}",headers=SBH,timeout=10)
print("[priority] removed")
requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
    json={"item_id":ITEM,"account":"ASVA","reason":"dejar agotar stock Full sin reactivar"},timeout=10)
print("[no_replenish] added — bot won't auto-revive when Full stock = 0")
requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"ASVA","scope":"item","scope_value":ITEM,
          "directive_type":"no_replenish","value_numeric":None,"raw_user_message":USER_MSG},timeout=10)
print("[directive] registered")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"\n[AFTER] status={g2.get('status')} qty={g2.get('available_quantity')} sub={g2.get('sub_status')}")
print(f"Permalink: {g2.get('permalink')}")
