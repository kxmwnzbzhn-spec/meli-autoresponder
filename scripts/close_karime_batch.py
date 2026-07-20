import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json"}

for iid in ["MLM3129626365","MLM5705924478"]:
    r=requests.delete(f"{sb_url}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=sh,timeout=10)
    print(f"{iid} priority DELETE: {r.status_code}",flush=True)
    row={"item_id":iid,"account":"KARIME","reason":"user pidió pausar + block 2026-07-19"}
    r=requests.post(f"{sb_url}/rest/v1/meli_no_replenish_items",headers={**sh,"Prefer":"resolution=merge-duplicates"},json=row,timeout=10)
    print(f"{iid} no_replenish INSERT: {r.status_code}",flush=True)
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status",headers=H,timeout=10).json()
    before=g.get("status")
    if before=="active":
        pr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
        print(f"  {iid} {before} -> {pr.get('status')} err={pr.get('message','')}",flush=True)
    else:
        print(f"  {iid} already {before}",flush=True)
    time.sleep(0.5)

# Verify
print(f"\n=== VERIFY ===",flush=True)
for iid in ["MLM3129626365","MLM5705924478"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,sub_status",headers=H,timeout=10).json()
    print(f"  {iid}: status={g.get('status')} sub={g.get('sub_status')}",flush=True)
