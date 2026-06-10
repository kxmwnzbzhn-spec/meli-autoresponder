import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
CPID=os.environ["CPID"]
p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"name: {p.get('name')}")
print(f"family_name: {p.get('family_name')}")
print(f"domain_id: {p.get('domain_id')}")
print(f"\n=== Attributes ===")
for a in (p.get("attributes") or []):
    print(f"  {a.get('id')}: name='{a.get('value_name')}' id={a.get('value_id')}")
print(f"\n=== Pictures ({len(p.get('pictures') or [])}) ===")
for pic in (p.get("pictures") or []):
    print(f"  {pic.get('url')}")
if p.get("short_description"):
    print(f"\n=== Description ===")
    print((p.get("short_description") or {}).get("content","")[:1000])
