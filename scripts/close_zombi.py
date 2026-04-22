import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

ZOMBI="MLM2883448233"
r1=requests.put(f"https://api.mercadolibre.com/items/{ZOMBI}",headers=H,json={"status":"closed"},timeout=15)
print(f"close {ZOMBI}: {r1.status_code}")
r2=requests.put(f"https://api.mercadolibre.com/items/{ZOMBI}",headers=H,json={"deleted":"true"},timeout=15)
print(f"delete: {r2.status_code}")

# Agregar al stock_config como deleted para que el bot no lo toque
with open("stock_config.json") as f: sc=json.load(f)
sc[ZOMBI]={"real_stock":0,"sku":"ZOMBI-Go4-Camuflaje","label":"Zombi Go 4 Camuflaje relisted","auto_replenish":False,"deleted":True}
# Tambien asegurarse que MLM2880762615 sigue con deleted=true auto_replenish=false
if "MLM2880762615" in sc:
    sc["MLM2880762615"]["auto_replenish"]=False
    sc["MLM2880762615"]["deleted"]=True
    sc["MLM2880762615"]["real_stock"]=0
with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print("stock_config.json actualizado: ZOMBI bloqueado, MLM2880762615 reconfirmado OFF")

# Verificar que NINGUNA Go 4 excepto la unificada tenga auto_replenish=True
print("\n=== Verificacion final ===")
on=[]
for iid,cfg in sc.items():
    if isinstance(cfg,dict) and cfg.get("auto_replenish",False):
        on.append((iid,cfg))
for iid,cfg in on:
    print(f"  ON {iid} | stock={cfg.get('real_stock')} | {cfg.get('label','')[:50]}")
