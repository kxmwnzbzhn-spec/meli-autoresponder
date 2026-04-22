import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# Stock confirmado por usuario en Bodega Electronica
STOCKS={
    "Negro":    200,   # user: "negro 200"
    "Azul":     499,   # user: "go4 azul tenemos 499"
    "Rojo":     0,     # no stock nuevo en file, user no menciono Rojo
    "Camuflaje":537,   # user: "camuflaje 537"
    "Rosa":     128,   # user: "rosa 128"
    "Aqua":     1037,  # user: SKU MLM2747271435 Agua = 1037
}

with open("stock_config.json") as f: sc=json.load(f)
cfg=sc.get(IID,{})
vars_cfg=cfg.setdefault("variations",{})

print("=== Update Go 4 stock per variation ===")
for color,new_stock in STOCKS.items():
    old=vars_cfg.get(color,{}).get("stock","-")
    vars_cfg[color]={"stock":new_stock,"orig_id":vars_cfg.get(color,{}).get("orig_id","")}
    print(f"  {color:<12} {old} -> {new_stock}")

total=sum(v.get("stock",0) for v in vars_cfg.values())
cfg["real_stock"]=total
sc[IID]=cfg
with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\nStock real TOTAL: {total} unidades")

# Verificar que todas las variaciones en MELI estén con qty>=1 (si hay stock)
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
current_vars=it.get("variations",[])
need_update=False
new_vars=[]
for v in current_vars:
    ac=v.get("attribute_combinations",[])
    color=ac[0].get("value_name","") if ac else ""
    cur_qty=v.get("available_quantity",0)
    real=STOCKS.get(color,0)
    target=1 if real>0 else 0
    if cur_qty != target:
        need_update=True
    nv={"id":v.get("id"),"price":v.get("price"),"available_quantity":target,"attribute_combinations":ac}
    if v.get("attributes"): nv["attributes"]=v["attributes"]
    if v.get("picture_ids"): nv["picture_ids"]=v["picture_ids"]
    new_vars.append(nv)

if need_update:
    all_var_pics=set()
    for v in current_vars:
        for pid in (v.get("picture_ids") or []): all_var_pics.add(pid)
    item_top_pics=[p.get("id") for p in it.get("pictures",[]) if p.get("id")]
    all_pics=list(dict.fromkeys(list(all_var_pics)+item_top_pics))
    r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"pictures":[{"id":p} for p in all_pics],"variations":new_vars},timeout=30)
    print(f"\nPUT variations sync: {r.status_code}")
    if r.status_code in (200,201):
        for v in r.json().get("variations",[]):
            ac=v.get("attribute_combinations",[])
            col=ac[0].get("value_name","") if ac else ""
            print(f"  {col}: qty={v.get('available_quantity')}")
