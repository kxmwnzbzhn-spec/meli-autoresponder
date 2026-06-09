import os, requests
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM=os.environ["ITEM"]
USER_MSG=f"pausa este en adrian {ITEM[3:] if ITEM.startswith('MLM') else ITEM}"
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} qty={g.get('available_quantity')} title={(g.get('title') or '')[:80]}")

rp=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"status":"paused"},timeout=15)
print(f"[PAUSE] HTTP {rp.status_code}: {rp.text[:200]}")

requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{ITEM}",headers=SBH,timeout=10)
requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
    json={"item_id":ITEM,"account":"ADRIAN","reason":"pausa manual usuario"},timeout=10)
requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"ADRIAN","scope":"item","scope_value":ITEM,
          "directive_type":"pause","value_numeric":None,"raw_user_message":USER_MSG},timeout=10)
print("[SUPABASE] priority removed + no_replenish + directive logged")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[AFTER] status={g2.get('status')} sub={g2.get('sub_status')}")
