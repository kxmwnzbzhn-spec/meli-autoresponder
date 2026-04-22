import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
sid=me.get("id")
print(f"Cuenta: {me.get('nickname')} id={sid}")

# Traer todos active
ids=[]
for st in ["active","under_review","paused"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break
print(f"Total items a evaluar: {len(ids)}")

paused=0; activated=0; skip=0; err=0
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,status,sub_status",headers=H,timeout=20).json()
    for x in res:
        b=x.get("body",{})
        if not b: continue
        iid=b.get("id"); title=b.get("title","") or ""; cur_status=b.get("status")
        ss=b.get("sub_status") or []
        ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
        
        t_lower = title.lower()
        is_go4 = ("go 4" in t_lower or "go4" in t_lower) and "go essential" not in t_lower
        
        # skip ya closed/deleted/inactive
        if cur_status in ("closed","inactive") or "deleted" in ss_str:
            skip+=1; continue
        
        if is_go4:
            # activar si está paused
            if cur_status == "paused":
                r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active"},timeout=15)
                if r.status_code in (200,201):
                    print(f"  ACTIVATE {iid} | {title[:55]}")
                    activated+=1
                else:
                    err+=1
            else:
                # ya active/under_review — no tocar
                print(f"  KEEP Go4 {iid} ({cur_status}) | {title[:55]}")
                skip+=1
        else:
            # pausar si está active
            if cur_status == "active":
                r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
                if r.status_code in (200,201):
                    print(f"  PAUSE {iid} | {title[:55]}")
                    paused+=1
                else:
                    print(f"  ERR pause {iid}: {r.status_code} {r.text[:100]}")
                    err+=1
            else:
                skip+=1
        time.sleep(0.3)

print(f"\n=== {paused} pausados, {activated} activados, {skip} skip, {err} errores ===")
