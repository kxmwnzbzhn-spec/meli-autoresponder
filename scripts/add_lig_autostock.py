import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LIGIA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LIGIA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=["MLM3152563611","MLM5745385304"]

# Fetch details
info=[]
for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,status,available_quantity,price,seller_id",headers=H,timeout=10).json()
    print(f"\n{iid}: status={g.get('status')} qty={g.get('available_quantity')} price=${g.get('price')} title={(g.get('title') or '?')[:60]}",flush=True)
    print(f"  seller_id: {g.get('seller_id')}",flush=True)
    if g.get("seller_id")!=3527910587:
        print(f"  ⚠️ WARNING: item no es de LIGIA (seller {g.get('seller_id')})",flush=True)
    info.append({"iid":iid,"title":g.get("title","?"),"status":g.get("status"),"qty":g.get("available_quantity")})

# Insert to Supabase priority_replenish
sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=representation"}

for it in info:
    row={
        "item_id":it["iid"],"account":"LIGIA","default_qty":1,
        "product_name":(it["title"] or "?")[:80],
        "reason":"user pidió activar autostock 2026-07-18"
    }
    r=requests.post(f"{sb_url}/rest/v1/meli_priority_replenish",headers=sh,json=row,timeout=15)
    print(f"\n{it['iid']} Supabase INSERT: {r.status_code}",flush=True)
    if r.status_code>=400:
        print(f"  err: {r.text[:300]}",flush=True)

# Also make sure not in no_replenish
for iid in ITEMS:
    r=requests.delete(f"{sb_url}/rest/v1/meli_no_replenish_items?item_id=eq.{iid}",headers=sh,timeout=10)
    print(f"  {iid} removed from no_replenish: {r.status_code}",flush=True)

# Update Ligia token
r=requests.patch(f"{sb_url}/rest/v1/meli_tokens?account=eq.LIGIA",headers=sh,json={"refresh_token":r.text if False else os.environ["MELI_REFRESH_TOKEN_LIGIA"]},timeout=10)

# Test simulation: force PUT active + qty=1 to verify bot logic works
print(f"\n=== TEST SIMULATION ===",flush=True)
for iid in ITEMS:
    tr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","available_quantity":1},timeout=15).json()
    if tr.get("error"):
        print(f"  {iid} ⚠️ err: {tr.get('message','?')[:150]}",flush=True)
    else:
        print(f"  {iid} ✅ status={tr.get('status')} qty={tr.get('available_quantity')}",flush=True)

# Verify Supabase state
r=requests.get(f"{sb_url}/rest/v1/meli_priority_replenish?item_id=in.({','.join(ITEMS)})&select=item_id,default_qty,product_name",headers=sh,timeout=10)
print(f"\n=== FINAL Supabase verify ===",flush=True)
print(r.text[:800],flush=True)
