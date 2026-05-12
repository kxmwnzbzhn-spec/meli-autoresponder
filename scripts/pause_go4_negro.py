import os,json,requests,base64
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ.get("GH_TOKEN") or ""
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
# scan all items
ids=[]
for st in ["active","paused"]:
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H).json()
        res=r.get("results",[]); 
        if not res: break
        ids+=res; off+=100
        if off>=r.get("paging",{}).get("total",0): break
matches=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,status,sub_status,available_quantity,price",headers=H).json()
    for x in r:
        b=x.get("body",{}) or {}
        t=(b.get("title") or "").lower()
        # match Go 4 with negro/negra
        if ("go 4" in t or "go4" in t or "go-4" in t) and ("negr" in t):
            matches.append(b)
print(f"Found {len(matches)} Go 4 Negro items:")
for m in matches:
    print(f"  {m['id']} st={m.get('status')} sub={m.get('sub_status')} qty={m.get('available_quantity')} ${m.get('price')} {m.get('title','')[:60]}")
# pause each
for m in matches:
    if m.get("status")=="active":
        r=requests.put(f"https://api.mercadolibre.com/items/{m['id']}",headers=H,json={"status":"paused"})
        print(f"  PAUSE {m['id']} http={r.status_code}")
print("---CFG_UPDATE---")
# Update config
if GHT:
    repo=f"{os.environ.get('REPO_OWNER','kxmwnzbzhn-spec')}/meli-autoresponder"
    g=requests.get(f"https://api.github.com/repos/{repo}/contents/stock_config_wilbert.json",headers={"Authorization":f"Bearer {GHT}"}).json()
    cfg=json.loads(base64.b64decode(g["content"]))
    for m in matches:
        iid=m["id"]
        cfg.setdefault(iid,{})
        cfg[iid]["real_stock"]=0
        cfg[iid]["master_stock"]=0
        cfg[iid]["min_visible"]=0
        cfg[iid]["available_quantity"]=0
        cfg[iid]["auto_replenish"]=False
        cfg[iid]["active"]=False
        cfg[iid]["agotado"]=True
        cfg[iid]["paused_by_user"]=True
        cfg[iid]["floor_locked_by_user"]=True
        print(f"  CFG_SET {iid}")
    new_b64=base64.b64encode(json.dumps(cfg,indent=2).encode()).decode()
    up=requests.put(f"https://api.github.com/repos/{repo}/contents/stock_config_wilbert.json",headers={"Authorization":f"Bearer {GHT}","Content-Type":"application/json"},json={"message":"Go4 Negro: sin stock, pause+agotado","content":new_b64,"sha":g["sha"]})
    print("  CFG_COMMIT:",up.status_code)
print("---DONE---")
