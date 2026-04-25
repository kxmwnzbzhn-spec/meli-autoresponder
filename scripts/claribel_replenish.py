import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

try: cfg=json.load(open("stock_config_claribel.json"))
except: cfg={}

for iid,info in cfg.items():
    if not info.get("active"): continue
    if not info.get("auto_replenish",True): continue
    
    cur=requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H).json()
    if cur.get("status") not in ("active","paused"): continue
    
    print(f"\n  {iid}: '{cur.get('title','')[:50]}'")
    
    if cur.get("variations"):
        new_vars=[]
        any_repuesto=False
        for v in cur.get("variations") or []:
            color=None
            for ac in v.get("attribute_combinations",[]):
                if ac.get("id")=="COLOR": color=ac.get("value_name"); break
            curr=v.get("available_quantity",0)
            real_stock=info.get("variations",{}).get(color,0)
            
            print(f"    {color} visible={curr} real={real_stock}")
            
            if curr==0 and real_stock>0:
                # repon visible a 1
                nv={
                    "id":v.get("id"),"price":v.get("price"),"available_quantity":1,
                    "attribute_combinations":v.get("attribute_combinations",[]),
                    "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
                }
                new_vars.append(nv)
                # decrementar stock real
                info["variations"][color]=real_stock-1
                any_repuesto=True
                print(f"      -> REPUESTO visible=1, real={real_stock-1}")
            else:
                nv={
                    "id":v.get("id"),"price":v.get("price"),"available_quantity":curr,
                    "attribute_combinations":v.get("attribute_combinations",[]),
                    "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
                }
                new_vars.append(nv)
        
        if any_repuesto:
            rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"variations":new_vars},timeout=30)
            print(f"    update: {rp.status_code}")

json.dump(cfg,open("stock_config_claribel.json","w"),indent=2,ensure_ascii=False)
print("\nDone")

