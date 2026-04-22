import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# Ya tenemos los pic IDs subidos
AQUA_PICS=["648339-MLM109860998910_042026","781235-MLM110758127029_042026","792029-MLM110758395587_042026","868941-MLM110760237981_042026"]

# Traer item actual
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()

# Pictures actuales (todos IDs del item top-level)
current_pics=[p.get("id") for p in it.get("pictures",[]) if p.get("id")]
print(f"Item pics actuales: {len(current_pics)}")

# Juntar: existentes + nuevas aqua
all_pics=current_pics+AQUA_PICS
# MELI limita 12 fotos — podamos
all_pics=all_pics[:12]
print(f"Total pics final: {len(all_pics)}")

# Variations existentes + agregar Aqua
current_vars=it.get("variations",[])
new_vars=[]
for v in current_vars:
    nv={
        "id":v.get("id"),
        "price":v.get("price"),
        "available_quantity":v.get("available_quantity"),
        "attribute_combinations":v.get("attribute_combinations",[])
    }
    if v.get("picture_ids"): nv["picture_ids"]=v["picture_ids"]
    new_vars.append(nv)

new_vars.append({
    "price":499,
    "available_quantity":1,
    "attribute_combinations":[{"id":"COLOR","value_name":"Aqua"}],
    "picture_ids":AQUA_PICS
})

body={
    "pictures":[{"id":pid} for pid in all_pics],
    "variations":new_vars
}
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)
print(f"PUT: {r.status_code}")
if r.status_code not in (200,201):
    print(r.text[:500])
else:
    resp=r.json()
    print(f"Variations ahora: {len(resp.get('variations',[]))}")
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"  {v.get('id')} {col} qty={v.get('available_quantity')} pics={len(v.get('picture_ids',[]))}")
    
    import json
    with open("stock_config.json") as f: sc=json.load(f)
    if IID in sc:
        vars_cfg=sc[IID].setdefault("variations",{})
        vars_cfg["Aqua"]={"stock":1037,"orig_id":"MLM2747271435"}
        sc[IID]["real_stock"]=sum(v.get("stock",0) for v in vars_cfg.values())
        with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
        print(f"stock_config total: {sc[IID]['real_stock']}")
