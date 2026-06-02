"""Final hunt — try domain specs, catalog product family, system-level charts."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

for ep in [
    "/domains/MLM-UNDERPANTS",
    "/domains/MLM-UNDERPANTS/specs?spec=charts",
    "/domains/MLM-UNDERPANTS/specs?spec=size_guides",
    "/sites/MLM/domains/MLM-UNDERPANTS",
    "/catalog_domains/MLM-UNDERPANTS",
    "/catalog_domains/MLM-UNDERPANTS/grids",
    "/grids?domain_id=MLM-UNDERPANTS&site_id=MLM",
    "/charts?domain_id=MLM-UNDERPANTS&site_id=MLM",
    # try the catalog product family
    "/families/Calvin%20Klein%20Brief/charts",
    # try public domain attribute charts
    "/categories/MLM194115/attributes/SIZE_GRID_ID",
    "/categories/MLM194115/attributes/SIZE_GRID_ID/values",
]:
    rr=requests.get(f"{API}{ep}",headers=H,timeout=12)
    snippet=rr.text[:300].replace("\n"," ")
    print(f"GET {ep} → HTTP {rr.status_code} | {snippet}")

# Try GET on a generic chart UUID just to see error format
print("\n--- example GET on random UUID")
rr=requests.get(f"{API}/catalog_charts/00000000-0000-0000-0000-000000000000",headers=H,timeout=8)
print(f"  → HTTP {rr.status_code}: {rr.text[:200]}")
