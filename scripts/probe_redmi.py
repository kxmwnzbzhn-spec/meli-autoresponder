import os, requests, json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

g=requests.get(f"{API}/items/MLM2940664057",headers=H,timeout=10).json()
print("=== MLM2940664057 (Yiriam, origen) ===")
print(f"  title: {g.get('title')}")
print(f"  category: {g.get('category_id')}  domain: {g.get('domain_id')}")
print(f"  price: {g.get('price')}  qty: {g.get('available_quantity')}  status: {g.get('status')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  catalog_listing: {g.get('catalog_listing')}")
print(f"  listing_type: {g.get('listing_type_id')}")
print(f"  pictures: {[p.get('id') for p in (g.get('pictures') or [])]}")
print(f"  attributes:")
for a in (g.get("attributes") or []):
    vn=a.get("value_name")
    if vn and a.get("id") in ("BRAND","MODEL","LINE","COLOR","GTIN","MODEL_CODE","ANATEL_HOMOLOGATION_NUMBER"):
        print(f"    {a.get('id')}={vn}")

# Buscar catalog product para este item (Redmi Buds 4 Lite)
print("\n=== Buscar catalog product ===")
title=g.get('title')
# Domain search
ds=requests.get(f"{API}/products/search",headers=H,params={"status":"active","site_id":"MLM","q":"Redmi Buds 4 Lite"},timeout=10).json()
results=ds.get("results") or []
print(f"  resultados: {len(results)}")
for r in results[:6]:
    pid=r.get("id"); 
    pd=requests.get(f"{API}/products/{pid}",headers=H,timeout=8).json()
    print(f"    {pid}  '{pd.get('name','')[:60]}'")
