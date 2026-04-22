import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Buscar catalog JBL Go 4 "Azul con Rosa" o "Agua" (color duotone)
for q in ["JBL Go 4 Azul Rosa","JBL Go 4 Agua","JBL Go 4 Summer","JBL Go 4 Duotone","JBL Go 4 Azul y Rosa"]:
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q.replace(' ','+')}",headers=H,timeout=15).json()
    print(f"\nSearch '{q}': {len(r.get('results',[]))} results")
    for it in r.get("results",[])[:6]:
        print(f"  {it.get('id')} | {it.get('name','')}")
