import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
sid=me.get("id")

# Buscar todas las publicaciones Go 4 en Juan
ids=[]
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
go4_negra=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,status,sub_status,condition",headers=H,timeout=20).json()
    for x in res:
        b=x.get("body",{})
        if not b: continue
        t=(b.get("title") or "").lower()
        if ("go 4" in t or "go4" in t) and ("negra" in t or "negro" in t or "black" in t) and "go essential" not in t:
            go4_negra.append(b)

print(f"\n=== Go 4 Negra encontradas: {len(go4_negra)} ===")
for b in go4_negra:
    ss=b.get("sub_status") or []
    ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
    print(f"  {b.get('id')} | {b.get('status')}/{ss_str} | cond={b.get('condition')} | {b.get('title','')[:60]}")

# Activar las NUEVAS (condition=new) que estén paused
print("\n=== Activando NUEVAS ===")
for b in go4_negra:
    iid=b.get("id")
    cond=b.get("condition")
    cur=b.get("status")
    ss=b.get("sub_status") or []
    ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
    if cond=="new" and cur=="paused":
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active"},timeout=15)
        print(f"  ACTIVATE {iid}: {r.status_code} {r.text[:120] if r.status_code>=400 else 'OK'}")
    elif cond=="new":
        print(f"  SKIP {iid} cond={cond} status={cur}/{ss_str}")
    time.sleep(0.3)
