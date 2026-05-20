"""Publicar catalog MLM69794803 en ASVA a $798"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# 1) Probe catalog product
p=requests.get(f"{API}/products/MLM69794803",headers=H,timeout=10).json()
name=p.get("name") or ""
domain=p.get("domain_id") or ""
print(f"=== Product MLM69794803 ===")
print(f"  name='{name}' domain={domain}")

# Find a category from any active listing of this product
pi=requests.get(f"{API}/products/MLM69794803/items?limit=5",headers=H,timeout=10).json()
results=pi.get("results") or []
cat_id=None
for r in results:
    rid=r.get("item_id") or r.get("id")
    if rid:
        g=requests.get(f"{API}/items/{rid}",headers=H,timeout=8).json()
        if g.get("category_id"):
            cat_id=g.get("category_id")
            print(f"  inherited category from {rid}: {cat_id}")
            break

# Lista competidores
print(f"\n=== Competidores ({len(results)}) ===")
for r in sorted(results,key=lambda x: x.get('price') or 99999):
    rid=r.get("item_id") or r.get("id")
    print(f"  {rid:<14} ${r.get('price'):>8} sold={r.get('sold_quantity',0)} ship_free={r.get('shipping',{}).get('free_shipping')}")

# 2) Publish
payload={
    "site_id":"MLM",
    "title": name[:60] if name else "Producto Catalog",
    "category_id": cat_id,
    "price":798,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "catalog_product_id":"MLM69794803",
    "catalog_listing":True,
}
print(f"\n=== Publicando a $798 (cat={cat_id}) ===")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    new_id=r.json().get("id")
    print(f"  NEW: {new_id}")
    time.sleep(2)
    pw=requests.get(f"{API}/items/{new_id}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: {pw.get('status')} ptw={pw.get('price_to_win')}")
else:
    print(f"  body={r.text[:800]}")
