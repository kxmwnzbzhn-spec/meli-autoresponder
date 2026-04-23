import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","api-version":"1","Content-Type":"application/json"}

# Obtener advertiser IDs
d=requests.get("https://api.mercadolibre.com/advertising/advertisers?product_id=PADS",headers=H).json()
print("advertisers:",json.dumps(d,ensure_ascii=False)[:2000])

advs=d.get("advertisers") or []
ITEMS={"Negro":"MLM5233480022","Azul":"MLM5233454100","Rojo":"MLM2886030837","Morado":"MLM2886136351"}

if advs:
    ADV_ID=advs[0]["advertiser_id"]
    print(f"\nADV_ID: {ADV_ID}")
    # Listar campañas existentes
    rc=requests.get(f"https://api.mercadolibre.com/advertising/advertisers/{ADV_ID}/product_ads/campaigns",headers=H,timeout=15)
    print(f"list campaigns: {rc.status_code}")
    if rc.status_code==200:
        print(json.dumps(rc.json(),ensure_ascii=False)[:1500])
    # Crear campaña
    body={"name":"ASVA Flip7 Genericas - Arranque Abr2026","status":"active","acos_target":"0.25","daily_budget":150,"channel":"marketplace","strategy":"profitability","site_id":"MLM"}
    for path in [f"/advertising/advertisers/{ADV_ID}/product_ads/campaigns",
                 f"/advertising/product_ads/advertisers/{ADV_ID}/campaigns",
                 f"/advertising/advertisers/{ADV_ID}/campaigns"]:
        rp=requests.post(f"https://api.mercadolibre.com{path}",headers=H,json=body,timeout=30)
        print(f"POST {path}: {rp.status_code}")
        if rp.status_code in (200,201):
            camp=rp.json()
            CAMP_ID=camp.get("id") or camp.get("campaign_id")
            print(f"  campaign_id={CAMP_ID}")
            for color,iid in ITEMS.items():
                for addpath in [f"/advertising/advertisers/{ADV_ID}/product_ads/campaigns/{CAMP_ID}/items",
                                f"/advertising/advertisers/{ADV_ID}/product_ads/items"]:
                    rb={"items":[{"id":iid,"status":"active"}]} if "items" in addpath and "campaigns" not in addpath else {"item_id":iid,"status":"active"}
                    rpa=requests.post(f"https://api.mercadolibre.com{addpath}",headers=H,json=rb,timeout=15)
                    if rpa.status_code in (200,201):
                        print(f"  add {color} via {addpath}: OK")
                        break
                    else:
                        print(f"  add {color} via {addpath}: {rpa.status_code} {rpa.text[:200]}")
            break
        else:
            print(f"  err: {rp.text[:400]}")
else:
    print("\n!!! ASVA no tiene advertiser registrado — activar MercadoAds en Seller Central manualmente !!!")
