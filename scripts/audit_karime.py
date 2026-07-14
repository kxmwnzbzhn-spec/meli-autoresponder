import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Load priority_replenish for KARIME from Supabase
sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}"}
pr=requests.get(f"{sb_url}/rest/v1/meli_priority_replenish?account=eq.KARIME&select=item_id,default_qty",headers=sh,timeout=10).json()
print(f"Priority items KARIME in DB: {len(pr)}",flush=True)
target_qty={p["item_id"]:p["default_qty"] for p in pr}

# All KARIME items
USER_ID=3527879962
all_ids=[]; offset=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?limit=50&offset={offset}",headers=H,timeout=15).json()
    ids=r.get("results",[])
    if not ids: break
    all_ids.extend(ids)
    if len(ids)<50: break
    offset+=50

fixed=0
skipped=0
for iid in all_ids:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,available_quantity,sub_status",headers=H,timeout=10).json()
    st=g.get("status")
    q=g.get("available_quantity") or 0
    sub=g.get("sub_status") or []
    tgt=target_qty.get(iid, 1)
    if st in ("closed","under_review"):
        continue
    # If active with qty>=target, skip
    if st=="active" and q>=tgt and "out_of_stock" not in sub:
        skipped+=1
        continue
    # Force active + target qty
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","available_quantity":tgt},timeout=15).json()
    if r.get("error"):
        print(f"  ❌ {iid} was st={st} q={q} sub={sub} → err: {r.get('message','?')[:100]}",flush=True)
    else:
        new_st=r.get("status"); new_q=r.get("available_quantity")
        print(f"  ✅ {iid} st={st}→{new_st} q={q}→{new_q} (tgt={tgt})",flush=True)
        fixed+=1
    time.sleep(0.4)

print(f"\nfixed={fixed} skipped={skipped}",flush=True)
