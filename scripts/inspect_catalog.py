"""Inspect catalog product MLM65349937: title, category, attributes, pictures, sizing info."""
import os, requests, json
API="https://api.mercadolibre.com"

# Use any token (catalog is read-only)
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}

CPID=os.environ.get("CPID","MLM65349937")
print(f"\n=== CATALOG PRODUCT {CPID} ===")
p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=20).json()
print(json.dumps({k:v for k,v in p.items() if k not in ("settings","short_description")}, indent=2)[:6000])

# Also get short description if any
if p.get("short_description"):
  print("\n[SHORT DESC]:")
  print(json.dumps(p["short_description"], indent=2)[:1500])

# Pictures
pics=p.get("pictures",[])
print(f"\n[PICTURES] count={len(pics)}")
for i,pic in enumerate(pics):
  print(f"  {i+1}: {pic.get('url') or pic.get('id')}  size={pic.get('size')} max_size={pic.get('max_size')}")

# Category requirements
cat=p.get("domain_id") or p.get("category_id")
print(f"\n[CATEGORY] {cat}")
if cat and cat.startswith("MLM"):
  cinfo=requests.get(f"{API}/categories/{cat}",headers=H,timeout=15).json()
  print(json.dumps({k:cinfo.get(k) for k in ("id","name","settings","attribute_types","children_categories")}, indent=2)[:2500])

# Try to get listing items in this catalog (for reference)
print("\n=== EXISTING LISTINGS in catalog (sample 3) ===")
li=requests.get(f"{API}/products/{CPID}/items?limit=3",headers=H,timeout=20).json()
for it in (li.get("results") or [])[:3]:
    iid=it.get("item_id") or it.get("id")
    g=requests.get(f"{API}/items/{iid}?attributes=id,title,listing_type_id,category_id,attributes,variations,sale_terms",headers=H,timeout=10).json()
    print(f"\n--- {iid} title={g.get('title')[:80]}")
    print(f"  listing_type={g.get('listing_type_id')} cat={g.get('category_id')}")
    sg=[a for a in (g.get("attributes") or []) if "SIZE" in (a.get("id") or "")]
    for a in sg: print(f"  attr {a.get('id')} = {a.get('value_name')} ({a.get('value_id')})")
    if g.get("variations"):
        v=g["variations"][0]
        print(f"  variations[0]: attribute_combinations={v.get('attribute_combinations')}")
