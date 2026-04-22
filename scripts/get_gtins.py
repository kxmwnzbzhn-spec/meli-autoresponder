import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

# Buscar catalogs con GTIN que tienen
CPIDS={"Charge 6 Azul":"MLM62088361","Charge 6 Roja":"MLM58806550","Charge 6 Negra":"MLM51435334","Charge 6 Camuflaje":"MLM58829227","Flip 7 Roja":"MLM48958711","Flip 7 Morada":"MLM49443139","Clip 5 Morada":"MLM45586155","Grip Negra":"MLM59802579","Go 4 Roja":"MLM64389753","Go 4 Rosa":"MLM65831856","Go 3 Negra":"MLM44709174","Go 4 Azul Marino":"MLM44731712"}
for label,cpid in CPIDS.items():
    p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    gtin=None; alphamod=None; ean=None; upc=None
    for a in (p.get("attributes") or []):
        if a.get("id")=="GTIN": gtin=a.get("value_name")
        if a.get("id")=="ALPHANUMERIC_MODEL": alphamod=a.get("value_name")
        if a.get("id")=="EAN": ean=a.get("value_name")
        if a.get("id")=="UPC": upc=a.get("value_name")
    print(f"{label}: gtin={gtin} ean={ean} upc={upc} model={alphamod}")
