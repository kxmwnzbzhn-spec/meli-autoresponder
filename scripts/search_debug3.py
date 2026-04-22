import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
# Con Bearer + User-Agent
H2={**H, "User-Agent":"Mozilla/5.0"}
r=requests.get("https://api.mercadolibre.com/sites/MLM/search?q=JBL%20Charge%206%20Roja&limit=10",headers=H2,timeout=20)
print(f"Status: {r.status_code}")
d=r.json()
print(f"Total: {d.get('paging',{}).get('total')}")
for it in d.get("results",[])[:10]:
    print(f"  {it.get('id')} | ${it.get('price')} | cond={it.get('condition')} | seller={it.get('seller',{}).get('id')} | {it.get('title','')[:70]}")
# Fallback: por catalog_product_id
print("\n--- /products/MLM58806550/items sin auth especial ---")
r3=requests.get("https://api.mercadolibre.com/products/MLM58806550/items",headers=H2,timeout=20)
print(f"{r3.status_code}: {r3.text[:400]}")
# /products/{id}?version=v2
print("\n--- /products/MLM58806550?include_children=true ---")
r4=requests.get("https://api.mercadolibre.com/products/MLM58806550?include_children=true",headers=H2,timeout=20).json()
print(f"bbw: {r4.get('buy_box_winner')}")
print(f"child ids: {r4.get('children_ids')}")
