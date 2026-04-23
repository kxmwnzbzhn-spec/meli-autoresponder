import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
it=requests.get("https://api.mercadolibre.com/items/MLM2883448187",headers=H,timeout=15).json()
# Ver family_name, user_product_id, y estructura clave
print(f"category_id: {it.get('category_id')}")
print(f"family_name: {it.get('family_name')}")
print(f"user_product_id: {it.get('user_product_id')}")
print(f"catalog_listing: {it.get('catalog_listing')}")
print(f"catalog_product_id: {it.get('catalog_product_id')}")
print(f"domain_id: {it.get('domain_id')}")
print(f"price top: {it.get('price')}")
print(f"qty top: {it.get('available_quantity')}")
print(f"variations {len(it.get('variations',[]))}:")
for v in it.get('variations',[])[:2]:
    print(f"  id={v.get('id')} upid={v.get('user_product_id')} gtin={[a for a in v.get('attributes',[]) if a.get('id')=='GTIN']}")
