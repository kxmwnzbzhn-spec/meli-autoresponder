import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Get all KARIME items
USER_ID=3527879962
all_ids=[]
offset=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?limit=50&offset={offset}",headers=H,timeout=15).json()
    ids=r.get("results",[])
    if not ids: break
    all_ids.extend(ids)
    if len(ids)<50: break
    offset+=50
print(f"Total: {len(all_ids)}",flush=True)

# Get status
items=[]
for i in range(0, len(all_ids), 20):
    batch=all_ids[i:i+20]
    r=requests.get(f"https://api.mercadolibre.com/items?ids={','.join(batch)}&attributes=id,status,available_quantity,price,sub_status,title",headers=H,timeout=15).json()
    for entry in r:
        b=entry.get("body",{})
        items.append({
            "iid":b.get("id"),"status":b.get("status"),"qty":b.get("available_quantity"),
            "price":b.get("price"),"sub":b.get("sub_status"),"title":(b.get("title") or "?")[:50]
        })

# Group
by_status={}
for it in items:
    s=it["status"]
    by_status.setdefault(s,[]).append(it)

print(f"\n=== STATUS BREAKDOWN ===",flush=True)
for s,lst in by_status.items():
    print(f"  {s}: {len(lst)}",flush=True)

print(f"\n=== ACTIVE items ({len(by_status.get('active',[]))}) ===",flush=True)
for it in by_status.get("active",[]):
    print(f"  {it['iid']} qty={it['qty']} ${it['price']} sub={it['sub']} | {it['title']}",flush=True)

print(f"\n=== PAUSED items ({len(by_status.get('paused',[]))}) ===",flush=True)
for it in by_status.get("paused",[]):
    print(f"  {it['iid']} qty={it['qty']} ${it['price']} sub={it['sub']} | {it['title']}",flush=True)

# Under review / other
for s in ["under_review","closed","inactive"]:
    lst=by_status.get(s,[])
    if lst:
        print(f"\n=== {s} ({len(lst)}) ===",flush=True)
        for it in lst[:5]:
            print(f"  {it['iid']} sub={it['sub']} | {it['title']}",flush=True)
