import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

# Ver TODAS las bocinas, su cpid real, y BBW de esos cpids
IDS=["MLM2880763001","MLM2880774951","MLM2880762579","MLM2880803051","MLM5223214318","MLM2880762535","MLM2880794089","MLM5223449418","MLM2880762595","MLM2880775007","MLM2880763019","MLM5223451400","MLM5223214798","MLM2880774949"]
for iid in IDS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    cpid=it.get("catalog_product_id")
    title=it.get("title","")
    price=it.get("price")
    print(f"\n{iid} | ${price} | cpid={cpid} | {title[:50]}")
    if cpid:
        p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
        bbw=p.get("buy_box_winner") or {}
        print(f"  cat_name: {p.get('name','')[:60]}")
        print(f"  bbw: item={bbw.get('item_id')} seller={bbw.get('seller_id')} price=${bbw.get('price')}")
