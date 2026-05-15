import os,json,base64,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
GHT=os.environ["GH_TOKEN"]
repo="kxmwnzbzhn-spec/meli-autoresponder"
g=requests.get(f"https://api.github.com/repos/{repo}/contents/stock_config_wilbert.json",headers={"Authorization":f"Bearer {GHT}"}).json()
cfg=json.loads(base64.b64decode(g["content"]))

# Get all Wilbert items with status
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
items={}
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,status,sub_status,available_quantity,price,sold_quantity",headers=H).json()
    for x in r:
        b=x.get("body",{}) or {}
        if b.get("id"): items[b["id"]]=b

# Categorize
print("=== Wilbert stock audit ===")
print(f"Total items active+paused: {len(items)}")
print()
print(f"{'MLM ID':<18} {'st':<6} {'sub':<22} {'vts':>4} {'visible':>7} {'real':>6} {'master':>6} {'flags':<30} title")
totals={"real":0,"sold":0,"by_modelo":{}}
def modelo_key(t):
    t=t.lower()
    if 'go 4' in t or 'go4' in t: return 'Go 4'
    if 'go 3' in t or 'go3' in t: return 'Go 3'
    if 'clip 5' in t or 'clip5' in t: return 'Clip 5'
    if 'clip 4' in t: return 'Clip 4'
    if 'charge 6' in t or 'charge6' in t: return 'Charge 6'
    if 'flip 7' in t or 'flip7' in t: return 'Flip 7'
    if 'grip' in t: return 'Grip'
    if 'xb100' in t or 'xb 100' in t: return 'XB100'
    if 'bose' in t or 'soundlink' in t: return 'Bose'
    return 'Perfume/Other'

for iid,b in sorted(items.items(),key=lambda x:-x[1].get("sold_quantity",0)):
    c=cfg.get(iid,{})
    flags=[]
    if c.get("agotado"): flags.append("AGOTADO")
    if c.get("paused_by_user"): flags.append("USER-PAUSED")
    if c.get("floor_locked_by_user"): flags.append("LOCKED")
    if c.get("closed"): flags.append("CLOSED")
    if not c: flags.append("NO-CFG")
    if not c.get("auto_replenish",True): flags.append("NO-REPL")
    real=c.get("real_stock",0)
    master=c.get("master_stock",0)
    sub=','.join(b.get('sub_status',[]) or [])
    print(f"{iid:<18} {b.get('status','?')[:6]:<6} {sub[:22]:<22} {b.get('sold_quantity',0):>4} {b.get('available_quantity',0):>7} {real:>6} {master:>6} {','.join(flags)[:30]:<30} {(b.get('title') or '')[:50]}")
    if not c.get("closed"):
        totals["real"]+=int(real or 0)
    totals["sold"]+=int(b.get("sold_quantity",0) or 0)
    mk=modelo_key(b.get('title',''))
    d=totals["by_modelo"].setdefault(mk,{"real":0,"items":0,"sold":0})
    if not c.get("closed"): d["real"]+=int(real or 0)
    d["items"]+=1
    d["sold"]+=int(b.get("sold_quantity",0) or 0)

print(f"\n=== TOTALES ===")
print(f"Stock real total (excluyendo closed): {totals['real']}")
print(f"Ventas históricas: {totals['sold']}")
print(f"\n=== Por modelo ===")
for mk,d in sorted(totals["by_modelo"].items(),key=lambda x:-x[1]['real']):
    print(f"  {mk:<15} real={d['real']:>4} items={d['items']:>3} vts_hist={d['sold']:>5}")
