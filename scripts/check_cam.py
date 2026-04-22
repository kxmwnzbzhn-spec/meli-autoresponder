import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Revisar MLM2880762615 y buscar cualquier otra Go 4 Camuflaje active/paused
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]
ids=[]
for st in ["active","paused","under_review","inactive"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break

cams=[]
for i in range(0,len(ids),20):
    b=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={b}&attributes=id,title,status,sub_status,price,available_quantity",headers=H,timeout=20).json()
    for x in res:
        bd=x.get("body",{})
        if not bd: continue
        t=(bd.get("title") or "").lower()
        if "camuflaje" in t and ("go 4" in t or "go4" in t):
            cams.append(bd)

print(f"=== Go 4 Camuflaje activas/pausadas: {len(cams)} ===")
for c in cams:
    ss=c.get("sub_status") or []
    ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
    print(f"  {c.get('id')} | {c.get('status')}/{ss_str} | ${c.get('price')} | qty={c.get('available_quantity')} | {c.get('title','')[:60]}")

# Revisar MLM2880762615 directamente
print("\n=== MLM2880762615 direct ===")
it=requests.get("https://api.mercadolibre.com/items/MLM2880762615",headers=H,timeout=15).json()
print(f"  status: {it.get('status')}/{it.get('sub_status')}")
print(f"  deleted: {it.get('deleted')}")
print(f"  qty: {it.get('available_quantity')}")

# Revisar la unificada
print("\n=== MLM2883448187 (unificada) ===")
un=requests.get("https://api.mercadolibre.com/items/MLM2883448187",headers=H,timeout=15).json()
print(f"  status: {un.get('status')}")
print(f"  variations:")
for v in un.get("variations",[]):
    ac=v.get("attribute_combinations",[])
    col = ac[0].get("value_name","") if ac else ""
    print(f"    id={v.get('id')} {col} qty={v.get('available_quantity')}")

# Revisar stock_config.json
print("\n=== stock_config.json Camuflaje entries ===")
with open("stock_config.json") as f: sc=json.load(f)
for iid,cfg in sc.items():
    if isinstance(cfg,dict):
        l=(cfg.get("label","") or "").lower()
        s=(cfg.get("sku","") or "").lower()
        if "camuflaje" in l or "camuflaje" in s or iid=="MLM2880762615":
            print(f"  {iid}: auto_replenish={cfg.get('auto_replenish')} deleted={cfg.get('deleted')} stock={cfg.get('real_stock')} label={cfg.get('label','')}")
