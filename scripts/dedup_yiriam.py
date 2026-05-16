import os,requests,json
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT_Y}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H).json()
        res=r.get("results",[])
        if not res: break
        ids+=res; off+=100
        if off>=r.get("paging",{}).get("total",0): break
print(f"Yiriam total: {len(ids)}")

# Get each item with date_created
items=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,catalog_product_id,date_created,price,status,sold_quantity",headers=H).json()
    for x in r:
        b=x.get("body",{}) or {}
        if b.get("id"): items.append(b)

# Group by CPID (or title if no CPID) → identify duplicates
by_key={}
for it in items:
    key=it.get("catalog_product_id") or it.get("title","")[:60]
    by_key.setdefault(key,[]).append(it)

duplicates=[]
for key,grp in by_key.items():
    if len(grp)<2: continue
    # Sort by date_created ascending — keep oldest, close newer ones (since user probably wants to preserve first)
    # Actually for our case (recently created in last run), close the ones with 0 sold and newest date
    grp.sort(key=lambda x:x.get("date_created",""))
    # Keep oldest (or one with most sold). Close rest if sold=0
    keep=grp[0]
    for it in grp[1:]:
        if it.get("sold_quantity",0)==0:
            duplicates.append({"close":it["id"],"keep":keep["id"],"title":(it.get("title") or "")[:50],"date":it.get("date_created","")[:10]})

print(f"\nDuplicados a cerrar: {len(duplicates)}")
for d in duplicates:
    print(f"  CLOSE {d['close']} (date={d['date']}) keep={d['keep']} '{d['title']}'")
    # pause first, then close
    r=requests.put(f"https://api.mercadolibre.com/items/{d['close']}",headers=H,json={"status":"paused"})
    r2=requests.put(f"https://api.mercadolibre.com/items/{d['close']}",headers=H,json={"status":"closed"})
    print(f"    pause={r.status_code} close={r2.status_code}")
