import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
# Search JBL Charge 6 Roja
r=requests.get("https://api.mercadolibre.com/sites/MLM/search?q=JBL%20Charge%206%20Roja&limit=15",headers=H,timeout=20).json()
for it in r.get("results",[])[:15]:
    print(f"  ${it.get('price')} | seller={it.get('seller',{}).get('id')} | cond={it.get('condition')} | {it.get('title','')[:70]}")
