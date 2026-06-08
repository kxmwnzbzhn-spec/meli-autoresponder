"""Detailed inspection of MLM146239 (Aceites Esenciales) for publishing rules."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

CAT="MLM146239"
ci=requests.get(f"{API}/categories/{CAT}",headers=H,timeout=10).json()
print(f"NAME: {ci.get('name')}")
print(f"PATH: {' > '.join(p.get('name','') for p in (ci.get('path_from_root') or []))}")
print(f"DOMAIN: {ci.get('settings',{}).get('catalog_domain')}")
print(f"\nSETTINGS:")
for k in ("item_conditions","buying_modes","max_title_length","max_pictures_per_item","minimum_price","maximum_price","mandatory_free_shipping"):
    print(f"  {k}: {ci.get('settings',{}).get(k)}")

print(f"\n=== ATTRIBUTES ===")
ca=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=10).json()
for a in ca:
    tags=a.get("tags") or {}
    req=tags.get("required",False)
    cat_req=tags.get("catalog_required",False)
    hidden=tags.get("hidden",False)
    vt=a.get("value_type")
    marker = "★ REQUIRED" if req else ("CAT_REQ" if cat_req else ("hidden" if hidden else ""))
    print(f"  {marker:14s} {a.get('id'):28s} {vt:14s} {a.get('name')}")
    if req or cat_req:
        vals=a.get("values") or []
        if vals:
            sample=[v.get("name") for v in vals[:6]]
            print(f"               sample: {sample}")
