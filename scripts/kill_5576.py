import os, requests
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
H={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

# Delete from priority_replenish
r=requests.delete(f"{SB}/rest/v1/meli_priority_replenish?item_id=eq.MLM5576391292",headers=H,timeout=8)
print(f"del priority: {r.status_code} body={r.text[:150]}")

# Ensure in no_replenish
r=requests.get(f"{SB}/rest/v1/meli_no_replenish_items?item_id=eq.MLM5576391292",headers=H,timeout=8)
print(f"check no_replenish: {r.status_code} body={r.text[:200]}")

if r.status_code==200 and r.text=='[]':
  r=requests.post(f"{SB}/rest/v1/meli_no_replenish_items",headers=H,
    json={"item_id":"MLM5576391292","reason":"PAUSADO DEFINITIVO 2026-07-03 - reemplazado por MLM5634575706 caja abierta $599 - NO REACTIVAR"},timeout=8)
  print(f"insert no_replenish: {r.status_code}")
