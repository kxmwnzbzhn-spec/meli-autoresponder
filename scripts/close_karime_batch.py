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

ITEMS=["MLM5706679194","MLM5706714904","MLM5706136704","MLM5706150254","MLM5706142768",
       "MLM5706138054","MLM3129625691","MLM5705924474","MLM5705924452","MLM3130262123"]

for iid in ITEMS:
    print(f"\n=== {iid} ===",flush=True)
    # 1) Quitar de priority (para que bot no interfiera)
    r=requests.delete(f"{sb_url}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=sh,timeout=10)
    # 2) Insertar en no_replenish
    row={"item_id":iid,"account":"KARIME","reason":"user pidió finalizar 2026-07-20"}
    r=requests.post(f"{sb_url}/rest/v1/meli_no_replenish_items",headers={**sh,"Prefer":"resolution=merge-duplicates"},json=row,timeout=10)
    
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,title",headers=H,timeout=10).json()
    before=g.get("status")
    title=(g.get("title") or "?")[:50]
    print(f"  before: {before} | {title}",flush=True)
    
    # 3) Pause first if active
    if before=="active":
        pr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
        pstat=pr.get("status")
        print(f"  paused: {pstat} err={pr.get('message','')}",flush=True)
        time.sleep(0.5)
    # 4) Close (irreversible)
    if before!="closed":
        cr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=10).json()
        cstat=cr.get("status")
        print(f"  closed: {cstat} err={cr.get('message','')}",flush=True)
    else:
        print(f"  already closed",flush=True)
    time.sleep(0.4)

# Final verify
print(f"\n=== FINAL VERIFY ===",flush=True)
for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status",headers=H,timeout=10).json()
    print(f"  {iid}: {g.get('status')}",flush=True)
