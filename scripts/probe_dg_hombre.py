"""Probe catalog product MLM47767674 + competidores actuales"""
import os, requests, json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

# Catalog product info
p=requests.get(f"{API}/products/MLM47767674",headers=H,timeout=10).json()
print(f"=== Product MLM47767674 ===")
print(f"  name: {p.get('name')}")
print(f"  domain: {p.get('domain_id')}")
print(f"  category: {(p.get('category_id'))}")
print(f"  status: {p.get('status')}")
attrs=p.get("attributes") or []
print(f"  attrs ({len(attrs)}):")
for a in attrs[:15]:
    print(f"    {a.get('id')}={a.get('value_name')}")

# Compet listings
pi=requests.get(f"{API}/products/MLM47767674/items?limit=20",headers=H,timeout=10).json()
results=pi.get("results") or []
print(f"\n=== Competidores ({len(results)}) ===")
for r in sorted(results,key=lambda x: x.get('price') or 99999):
    rid=r.get("item_id") or r.get("id")
    print(f"  {rid:<14} ${r.get('price'):>8} sold={r.get('sold_quantity',0)} ship_free={r.get('shipping',{}).get('free_shipping')} status={r.get('status')}")

# Verificar reference: MLM5363034852 (Women)
print(f"\n=== Current 5363034852 (Women, ref) ===")
g=requests.get(f"{API}/items/MLM5363034852",headers=H,timeout=10).json()
print(f"  status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')} cpid={g.get('catalog_product_id')}")
print(f"  inventory_id={g.get('inventory_id')} listing_type={g.get('listing_type_id')}")
print(f"  domain={g.get('domain_id')} cat={g.get('category_id')}")
print(f"  pics={[pic.get('id') for pic in (g.get('pictures') or [])][:3]}")
