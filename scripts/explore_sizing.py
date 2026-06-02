"""Explore MLM-CLOTHING_LOTS category + size chart options for S/M/L/XL."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}

# 1) Domain discovery: find leaf category for "paca boxers calvin klein"
print("\n=== DOMAIN DISCOVERY ===")
dd=requests.get(f"{API}/sites/MLM/domain_discovery/search",
                params={"q":"paca 3 boxers calvin klein microfibra","limit":5},headers=H,timeout=15).json()
print(json.dumps(dd, indent=2)[:3000])

# 2) Catalog domain charts
print("\n=== CHARTS for MLM-CLOTHING_LOTS ===")
ch=requests.get(f"{API}/catalog_domains/MLM-CLOTHING_LOTS/charts",headers=H,timeout=15).json()
print(json.dumps(ch, indent=2)[:3000])

# 3) Try fetching attributes required for the discovered category
if isinstance(dd,list) and dd:
    cat=dd[0].get("category_id")
    print(f"\n=== CATEGORY {cat} attributes ===")
    ca=requests.get(f"{API}/categories/{cat}/attributes",headers=H,timeout=15).json()
    # Only print required ones + size-related
    for a in ca:
        tags=a.get("tags") or {}
        if tags.get("required") or "SIZE" in (a.get("id") or "") or "TALLA" in (a.get("name") or "").upper() or "GTIN" in (a.get("id") or ""):
            print(f"  {a.get('id')} | required={tags.get('required',False)} | catalog_required={tags.get('catalog_required',False)} | type={a.get('value_type')} | name={a.get('name')}")
    # Settings
    print(f"\n=== CATEGORY {cat} info ===")
    ci=requests.get(f"{API}/categories/{cat}",headers=H,timeout=15).json()
    print(json.dumps({k:ci.get(k) for k in ("id","name","settings","path_from_root")}, indent=2)[:2500])

# 4) Check seller's existing user-level size charts
print("\n=== SELLER size charts ===")
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
sid=me.get("id")
sc=requests.get(f"{API}/users/{sid}/products/charts",headers=H,timeout=15)
print(f"HTTP {sc.status_code}: {sc.text[:2000]}")
