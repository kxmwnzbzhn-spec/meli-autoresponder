import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]

# TODAS sin filtro de status
ids=[]
s=0
while True:
    d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?limit=100&offset={s}",headers=H,timeout=20).json()
    got=d.get("results",[])
    if not got: break
    for i in got:
        if i not in ids: ids.append(i)
    s+=100
    if s>=d.get("paging",{}).get("total",0): break
for st in ["active","paused","under_review","closed","inactive"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break
print(f"Total items: {len(ids)}")

go4=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,status",headers=H,timeout=20).json()
    for x in res:
        b=x.get("body",{})
        if not b: continue
        t=(b.get("title") or "").lower()
        if ("go 4" in t or "go4" in t) and "go essential" not in t and b.get("status") in ("active","paused"):
            go4.append(b)

print(f"=== Go 4 activas/pausadas: {len(go4)} ===")
for b in go4:
    iid=b.get("id"); cur=b.get("price"); st=b.get("status")
    if cur != 499:
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":499},timeout=15)
        print(f"  {iid} ({st}) ${cur}->$499: {r.status_code}")
    else:
        print(f"  {iid} ({st}) ya en $499")
    time.sleep(0.3)
