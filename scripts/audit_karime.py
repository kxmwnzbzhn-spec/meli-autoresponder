import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

USER_ID=3527879962

# List all KARIME items - pagination
all_ids=[]
offset=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?limit=50&offset={offset}",headers=H,timeout=15).json()
    ids=r.get("results",[])
    if not ids: break
    all_ids.extend(ids)
    if len(ids)<50: break
    offset+=50

print(f"Total items in KARIME: {len(all_ids)}",flush=True)

# Get status for each - batch multiget
active_items=[]
inactive_items=[]
for i in range(0, len(all_ids), 20):
    batch=all_ids[i:i+20]
    r=requests.get(f"https://api.mercadolibre.com/items?ids={','.join(batch)}&attributes=id,title,status,available_quantity,price",headers=H,timeout=15).json()
    for entry in r:
        body=entry.get("body",{})
        iid=body.get("id")
        st=body.get("status")
        title=(body.get("title") or "?")[:60]
        qty=body.get("available_quantity") or 0
        price=body.get("price") or 0
        if st=="active":
            active_items.append((iid,title,qty,price))
        else:
            inactive_items.append((iid,title,st,qty))

print(f"\n=== ACTIVE ({len(active_items)}) ===",flush=True)
for iid,title,qty,price in active_items:
    print(f"  {iid} qty={qty} ${price} | {title}",flush=True)

print(f"\n=== NOT ACTIVE ({len(inactive_items)}) ===",flush=True)
for iid,title,st,qty in inactive_items[:20]:
    print(f"  {iid} {st} qty={qty} | {title}",flush=True)

# Print pipe-separated active ID list for Supabase
print(f"\nACTIVE_IDS: {','.join(x[0] for x in active_items)}",flush=True)
