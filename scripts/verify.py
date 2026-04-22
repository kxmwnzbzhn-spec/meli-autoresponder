import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
it=requests.get("https://api.mercadolibre.com/items/MLM2880877609",headers=H,timeout=15).json()
print(f"id: {it.get('id')}")
print(f"title: {it.get('title')}")
print(f"status: {it.get('status')}/{it.get('sub_status')}")
print(f"catalog_listing: {it.get('catalog_listing')}")
print(f"catalog_product_id: {it.get('catalog_product_id')}")
print(f"permalink: {it.get('permalink')}")
# Intentar cambiar pictures directamente con una URL de prueba
test_pics=[{"source":"https://http2.mlstatic.com/D_745511-MLA91413593851_092025-O.jpg"}]
test=requests.put("https://api.mercadolibre.com/items/MLM2880877609",headers={**H,"Content-Type":"application/json"},json={"pictures":test_pics},timeout=15)
print(f"\nTest PUT pictures: {test.status_code} {test.text[:300]}")
