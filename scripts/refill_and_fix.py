import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# Leer item actual
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
current_vars=it.get("variations",[])

# Leer stock config para saber stock_real por color
with open("stock_config.json") as f: sc=json.load(f)
vars_cfg=sc.get(IID,{}).get("variations",{}) or {}

# Reponer cada variation a qty=1 si stock_real>0 y qty actual=0
new_vars=[]
repuestas=[]
for v in current_vars:
    ac=v.get("attribute_combinations",[])
    color = ac[0].get("value_name","") if ac else ""
    cur_qty=v.get("available_quantity",0)
    stock_real=vars_cfg.get(color,{}).get("stock",0)
    
    nv={
        "id":v.get("id"),
        "price":v.get("price"),
        "attribute_combinations":v.get("attribute_combinations",[]),
    }
    if v.get("attributes"): nv["attributes"]=v["attributes"]
    if v.get("picture_ids"): nv["picture_ids"]=v["picture_ids"]
    
    # si qty==0 y stock_real>0 → reponer 1
    if cur_qty==0 and stock_real>0:
        nv["available_quantity"]=1
        repuestas.append(f"{color} (stock_real={stock_real})")
    else:
        nv["available_quantity"]=max(cur_qty,1) if stock_real>0 else 0
    new_vars.append(nv)

# Pics top-level
all_var_pics=set()
for v in current_vars:
    for pid in (v.get("picture_ids") or []): all_var_pics.add(pid)
item_top_pics=[p.get("id") for p in it.get("pictures",[]) if p.get("id")]
all_pics=list(dict.fromkeys(list(all_var_pics)+item_top_pics))

body={"pictures":[{"id":p} for p in all_pics],"variations":new_vars}
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)
print(f"PUT replenish: {r.status_code}")
if r.status_code in (200,201):
    print(f"Repuestas: {repuestas}")
    resp=r.json()
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"  {col}: qty={v.get('available_quantity')}")
else:
    print(r.text[:500])
