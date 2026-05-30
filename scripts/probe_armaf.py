import os, requests, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}

# Site search to find LIVE listings (sellers actually selling this product)
r=requests.get(f"{API}/sites/MLM/search",headers=H,params={"q":"Armaf Club De Nuit Maleka 105ml","limit":10,"status":"active"},timeout=20).json()
print(f"\nResults: {len(r.get('results') or [])}")
for it in (r.get("results") or [])[:5]:
    print(f"\n  {it.get('id')} {it.get('title')[:60]}")
    print(f"    seller_id={it.get('seller',{}).get('id')} price=${it.get('price')}")
    print(f"    category_id={it.get('category_id')}")
    print(f"    catalog_product_id={it.get('catalog_product_id')}")
    print(f"    catalog_listing={it.get('catalog_listing')}")

# Also try /products/{cpid}/items endpoint
print("\n=== /products/MLM50661134/items ===")
r2=requests.get(f"{API}/products/MLM50661134/items",headers=H,timeout=15).json()
print(f"results: {len(r2.get('results') or [])}")
for o in (r2.get("results") or [])[:3]:
    iid=o.get("item_id")
    print(f"\n  item_id={iid} price={o.get('price')} winner={o.get('winner')}")
    if iid:
        tmp=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        print(f"    title={tmp.get('title','')[:60]}")
        print(f"    category_id={tmp.get('category_id')}")
        print(f"    status={tmp.get('status')}")
