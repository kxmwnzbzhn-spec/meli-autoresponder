import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# 1) Stock REAL por item (lo que tiene el usuario de inventario)
REAL_STOCK={
    "MLM5235542250":{"Negro":50,"Azul":50,"Rojo":50,"Rosa":50,"Camuflaje":50,"Aqua":50},
    "MLM5241291642":{"Negro":50,"Azul":50,"Rojo":50,"Rosa":50,"Camuflaje":50,"Aqua":50},
}

# 2) Poner visible=1 en ambos items para escasez
for IID in REAL_STOCK:
    cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
    new_vars=[]
    for v in (cur.get("variations") or []):
        nv={
            "id":v.get("id"),"price":v.get("price"),"available_quantity":1,
            "attribute_combinations":v.get("attribute_combinations",[]),
            "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
        }
        new_vars.append(nv)
    rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"variations":new_vars},timeout=30)
    print(f"  {IID} visible=1: {rp.status_code}")

# 3) Actualizar config con stock real
cfg={}
for iid,colors in REAL_STOCK.items():
    cfg[iid]={
        "line":"Go4-Raymundo",
        "auto_replenish":True,
        "min_visible":1,
        "variations":colors,
        "active":True,
    }
json.dump(cfg,open("stock_config_raymundo.json","w"),indent=2,ensure_ascii=False)
print("\nstock_config_raymundo.json actualizado con stock real 50 por color en ambos items")
