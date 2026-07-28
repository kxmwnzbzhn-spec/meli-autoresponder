import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json"}

IID="MLM3166561687"
r=requests.delete(f"{sb_url}/rest/v1/meli_priority_replenish?item_id=eq.{IID}",headers=sh,timeout=10)
print(f"priority DELETE: {r.status_code}",flush=True)
row={"item_id":IID,"account":"ASVA","reason":"user pidió pausar + no reactivar por ahora 2026-07-27"}
r=requests.post(f"{sb_url}/rest/v1/meli_no_replenish_items",headers={**sh,"Prefer":"resolution=merge-duplicates"},json=row,timeout=10)
print(f"no_replenish INSERT: {r.status_code}",flush=True)

g=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status,title",headers=H,timeout=10).json()
before=g.get("status")
print(f"BEFORE: {before} | {(g.get('title') or '?')[:60]}",flush=True)
if before=="active":
    pr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"paused"},timeout=10).json()
    print(f"PAUSED: status={pr.get('status')} err={pr.get('message','')}",flush=True)

time.sleep(1)
g=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status,sub_status",headers=H,timeout=10).json()
print(f"VERIFY: status={g.get('status')} sub={g.get('sub_status')}",flush=True)
