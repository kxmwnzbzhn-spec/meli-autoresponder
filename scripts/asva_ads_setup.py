import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json","api-version":"1"}

# Obtener user_id
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"ASVA user_id: {USER_ID} | nickname: {me.get('nickname')}")

ITEMS={
    "Negro":"MLM5233480022",
    "Azul":"MLM5233454100",
    "Rojo":"MLM2886030837",
    "Morado":"MLM2886136351",
}

# 1) Verificar elegibilidad de cada item para Product Ads
print("\n=== ELEGIBILIDAD ===")
for color,iid in ITEMS.items():
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,tags,catalog_listing,listing_type_id,status,health,sold_quantity",headers=H).json()
    print(f"  {color} {iid}: status={d.get('status')} listing={d.get('listing_type_id')} catalog={d.get('catalog_listing')} tags={(d.get('tags') or [])[:4]}")

# 2) Intentar listar campanas existentes de product ads
print("\n=== CAMPANAS EXISTENTES ===")
for path in [f"/advertising/advertisers?product_id=PADS",
             f"/advertising/product_ads/campaigns",
             f"/product_ads/campaigns?site_id=MLM",
             f"/advertising/advertisers"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"  {path}: {rp.status_code}")
    if rp.status_code==200:
        print(f"    {json.dumps(rp.json(),ensure_ascii=False)[:500]}")
        break

# 3) Crear campaña Product Ads con ACOS 25% (rentabilidad) y presupuesto $150/dia
print("\n=== CREAR CAMPANA ===")
# endpoint actualizado
CAMPAIGN_BODY={
    "name":"ASVA Flip7 Genericas - Arranque Abr2026",
    "status":"active",
    "acos_target":25,
    "daily_budget":150,
    "channel":"marketplace",
    "strategy":"profitability",
    "site_id":"MLM",
}
# varias rutas alternas
for path in ["/advertising/product_ads/campaigns",
             f"/advertising/advertisers/{USER_ID}/campaigns",
             f"/product_ads/campaigns"]:
    rp=requests.post(f"https://api.mercadolibre.com{path}",headers=H,json=CAMPAIGN_BODY,timeout=30)
    print(f"  POST {path}: {rp.status_code}")
    if rp.status_code in (200,201):
        camp=rp.json()
        print(f"    campaign_id={camp.get('id') or camp.get('campaign_id')}")
        CAMP_ID=camp.get("id") or camp.get("campaign_id")
        # agregar items a la campaña
        for color,iid in ITEMS.items():
            rpa=requests.post(f"https://api.mercadolibre.com/advertising/product_ads/campaigns/{CAMP_ID}/items",
                              headers=H,json={"item_id":iid},timeout=15)
            print(f"    add {color} {iid}: {rpa.status_code}")
        break
    else:
        print(f"    {rp.text[:300]}")
