import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"Cuenta: {me.get('nickname')} id={me.get('id')}")

# Traer lista actual de perfumes en Juan
with open("juan_perfumes.json") as f: perfumes=json.load(f)
ids=[p.get("id") for p in perfumes if p.get("id")]
print(f"Perfumes a borrar: {len(ids)}")

closed=0; deleted=0; already=0; err=0
for iid in ids:
    # check current status
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    cur_status=it.get("status")
    ss=it.get("sub_status")
    ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
    if "deleted" in ss_str:
        already+=1
        continue
    # close
    if cur_status != "closed":
        r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=15)
        if r1.status_code in (200,201): closed+=1
    # delete
    r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"deleted":"true"},timeout=15)
    if r2.status_code in (200,201):
        deleted+=1
        print(f"  OK deleted {iid}")
    else:
        err+=1
        print(f"  ERR {iid}: {r2.status_code} {r2.text[:120]}")
    time.sleep(0.4)

print(f"\n=== {closed} cerrados, {deleted} eliminados, {already} ya deleted, {err} errores ===")

# Tambien desactivar auto_replenish en stock_config.json
try:
    with open("stock_config.json") as f: sc=json.load(f)
    changed=0
    for iid in ids:
        if iid in sc:
            sc[iid]["auto_replenish"]=False
            sc[iid]["deleted"]=True
            sc[iid]["real_stock"]=0
            changed+=1
    with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"stock_config.json: {changed} marcados deleted")
except Exception as e:
    print(f"stock_config err: {e}")
