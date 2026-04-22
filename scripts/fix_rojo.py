import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# Update stock_config
with open("stock_config.json") as f: sc=json.load(f)
cfg=sc.get(IID,{})
vars_cfg=cfg.setdefault("variations",{})
vars_cfg["Rojo"]={"stock":200,"orig_id":vars_cfg.get("Rojo",{}).get("orig_id","")}
cfg["real_stock"]=sum(v.get("stock",0) for v in vars_cfg.values())
sc[IID]=cfg
with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"Rojo -> 200 | Total stock: {cfg['real_stock']}")

# Sincronizar MELI: Rojo qty=0 -> qty=1
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
current_vars=it.get("variations",[])
new_vars=[]
for v in current_vars:
    ac=v.get("attribute_combinations",[])
    color=ac[0].get("value_name","") if ac else ""
    nv={"id":v.get("id"),"price":v.get("price"),"attribute_combinations":ac}
    if v.get("attributes"): nv["attributes"]=v["attributes"]
    if v.get("picture_ids"): nv["picture_ids"]=v["picture_ids"]
    if color=="Rojo":
        nv["available_quantity"]=1
    else:
        nv["available_quantity"]=v.get("available_quantity",0)
    new_vars.append(nv)

all_var_pics=set()
for v in current_vars:
    for pid in (v.get("picture_ids") or []): all_var_pics.add(pid)
item_top_pics=[p.get("id") for p in it.get("pictures",[]) if p.get("id")]
all_pics=list(dict.fromkeys(list(all_var_pics)+item_top_pics))

r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"pictures":[{"id":p} for p in all_pics],"variations":new_vars},timeout=30)
print(f"PUT: {r.status_code}")
if r.status_code in (200,201):
    for v in r.json().get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"  {col}: qty={v.get('available_quantity')}")
