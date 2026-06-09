import os, requests
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_AH={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM=os.environ["ITEM"]
USER_MSG=f"activa esto en adrian {ITEM[3:] if ITEM.startswith('MLM') else ITEM}"

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
print(f"  title={g.get('title')}")

payload={"status":"active"}
if (g.get("available_quantity") or 0)<1:
    payload["available_quantity"]=1

rr=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=payload,timeout=15)
print(f"[ACTIVATE payload={payload}] HTTP {rr.status_code}: {rr.text[:300]}")

# Remove from no_replenish lock so future bots can work
requests.delete(f"{SBU}/rest/v1/meli_no_replenish_items?item_id=eq.{ITEM}",headers=SBH,timeout=10)
print("[no_replenish] removed if existed")

# Add priority for auto-replenish (1 per sale)
requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
    json={"item_id":ITEM,"account":"ADRIAN","default_qty":max(g.get("available_quantity") or 1, 1),
          "product_name":(g.get("title") or "")[:200]},timeout=10)
print("[priority_replenish] upsert")

requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"ADRIAN","scope":"item","scope_value":ITEM,
          "directive_type":"activate","value_numeric":None,"raw_user_message":USER_MSG},timeout=10)
print("[directive] registered")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"\n[AFTER] status={g2.get('status')} qty={g2.get('available_quantity')}")
print(f"Permalink: {g2.get('permalink')}")
