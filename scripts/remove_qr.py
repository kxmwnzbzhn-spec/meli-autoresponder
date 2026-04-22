import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM2880877609"
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
print(f"Item: {it.get('title')}")
print(f"Status: {it.get('status')} catalog_listing={it.get('catalog_listing')}")
print(f"Catalog product: {it.get('catalog_product_id')}")
print("\nPictures:")
for i,p in enumerate(it.get("pictures",[])):
    print(f"  [{i}] id={p.get('id')} url={p.get('url')}")
