import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

IID="MLM2883448187"
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
print(f"=== Item {IID} ===")
print(f"title: {it.get('title')}")
print(f"status: {it.get('status')}/{it.get('sub_status')}")
print(f"condition: {it.get('condition')}")
print(f"listing_type: {it.get('listing_type_id')}")
print(f"catalog_listing: {it.get('catalog_listing')}")
print(f"catalog_product_id: {it.get('catalog_product_id')}")
print(f"category: {it.get('category_id')}")
print(f"available_quantity: {it.get('available_quantity')}")
print(f"variations: {len(it.get('variations',[]))}")
print(f"tags: {it.get('tags')}")
print(f"health: {it.get('health')}")
print(f"quality: {it.get('catalog_listing_status','')} / qualification:{it.get('qualification')}")
print(f"free_shipping: {it.get('shipping',{}).get('free_shipping')}")

# Item health / quality
for ep in [f"/items/{IID}/health",f"/items/{IID}/quality",f"/items/{IID}/visits"]:
    r2=requests.get(f"https://api.mercadolibre.com{ep}",headers=H,timeout=15)
    print(f"\n{ep}: {r2.status_code}")
    print(r2.text[:500])

# Variations
print("\n=== Variations ===")
for v in it.get("variations",[])[:10]:
    print(f"  id={v.get('id')} qty={v.get('available_quantity')} price={v.get('price')} attrs={[a.get('value_name') for a in v.get('attribute_combinations',[])]}")
