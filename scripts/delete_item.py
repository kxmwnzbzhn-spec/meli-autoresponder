import os,requests,json
IID="MLM5221973786"

# Intentar con ambos tokens
TOKENS=[("primary",os.environ.get("MELI_REFRESH_TOKEN")),("oficial",os.environ.get("MELI_REFRESH_TOKEN_OFICIAL"))]

for label,rt in TOKENS:
    if not rt: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r: continue
    H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
    it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
    if "error" in it: 
        print(f"[{label}] no encontrado: {it.get('error')}")
        continue
    print(f"[{label}] FOUND: {it.get('title')} status={it.get('status')}")
    # close
    r1=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"closed"},timeout=15)
    print(f"  close: {r1.status_code}")
    # delete
    r2=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"deleted":"true"},timeout=15)
    print(f"  delete: {r2.status_code}")
    
    # Actualizar ambos stock_config
    for cfg_file in ["stock_config.json","stock_config_oficial.json"]:
        try:
            with open(cfg_file) as f: sc=json.load(f)
            if IID in sc:
                sc[IID]["auto_replenish"]=False
                sc[IID]["deleted"]=True
                sc[IID]["real_stock"]=0
                with open(cfg_file,"w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
                print(f"  {cfg_file}: auto_replenish=false, deleted=true")
        except Exception as e:
            print(f"  {cfg_file}: {e}")
    break
