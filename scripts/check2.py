import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
for iid in ["MLM2879717657","MLM2880144815"]:
    r=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    print(f"\n=== {iid} ===")
    print(f"title: {r.get('title')}")
    print(f"price: ${r.get('price')}")
    print(f"status: {r.get('status')}/{r.get('sub_status')}")
    print(f"cat: {r.get('category_id')}")
    print(f"catalog_product_id: {r.get('catalog_product_id')}")
    print(f"pictures ({len(r.get('pictures',[]))}):")
    for p in (r.get('pictures') or [])[:5]:
        print(f"  {p.get('url')}")
    print(f"attrs:")
    for a in (r.get('attributes') or []):
        aid=a.get('id'); vn=a.get('value_name')
        if aid in ('BRAND','MODEL','COLOR','LINE','ALPHANUMERIC_MODEL','ITEM_CONDITION','GTIN'):
            print(f"  {aid}={vn}")
