import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"Raymundo: {me.get('nickname')} ({me.get('id')})")

# Items activos
s=requests.get(f"https://api.mercadolibre.com/users/{me['id']}/items/search?status=active&limit=50",headers=H).json()
items=s.get("results") or []
print(f"Items activos: {len(items)}")

# Cargar/crear config
try: cfg=json.load(open("stock_config_raymundo.json"))
except: cfg={}

for iid in items:
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H).json()
    print(f"\n  {iid}: '{d.get('title','')[:50]}'")
    
    # Si es item con variations
    if d.get("variations"):
        new_vars=[]
        any_repuesto=False
        for v in d.get("variations") or []:
            color=None
            for ac in v.get("attribute_combinations",[]):
                if ac.get("id")=="COLOR": color=ac.get("value_name"); break
            curr=v.get("available_quantity",0)
            # Si visible=0 y en config tenemos stock real >0, repon a 1
            cfg_item=cfg.get(iid,{})
            cfg_var=cfg_item.get("variations",{}).get(color,{}) if isinstance(cfg_item.get("variations"),dict) else {}
            real_stock=cfg_var.get("max",0) if isinstance(cfg_var,dict) else cfg_var
            
            print(f"    {color} visible={curr} real={real_stock}")
            
            if curr==0 and real_stock>0:
                # repon a 1
                nv={
                    "id":v.get("id"),"price":v.get("price"),"available_quantity":1,
                    "attribute_combinations":v.get("attribute_combinations",[]),
                    "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
                }
                new_vars.append(nv)
                # Decrementar stock real
                if isinstance(cfg_var,dict): cfg_var["max"]=real_stock-1
                any_repuesto=True
                print(f"      -> REPONIENDO a 1, real={real_stock-1}")
            else:
                # mantener intacto
                nv={
                    "id":v.get("id"),"price":v.get("price"),"available_quantity":curr,
                    "attribute_combinations":v.get("attribute_combinations",[]),
                    "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
                }
                new_vars.append(nv)
        
        if any_repuesto:
            rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"variations":new_vars},timeout=30)
            print(f"    update: {rp.status_code}")
    else:
        # single SKU
        curr=d.get("available_quantity",0)
        cfg_item=cfg.get(iid,{})
        real_stock=cfg_item.get("max",0) if isinstance(cfg_item,dict) else 0
        print(f"    visible={curr} real={real_stock}")
        if curr==0 and real_stock>0:
            rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":1},timeout=30)
            print(f"    update single: {rp.status_code}")
            cfg[iid]["max"]=real_stock-1

json.dump(cfg,open("stock_config_raymundo.json","w"),indent=2,ensure_ascii=False)
print("\nstock_config_raymundo.json actualizado")
