import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Minimal product POST attempts to see what's required/possible
attempts=[
  ("/products",{"name":"test","domain_id":"MLM-PERFUMES","attributes":[]}),
  ("/catalog/products",{"name":"test","domain_id":"MLM-PERFUMES","attributes":[]}),
  ("/catalog_listings",{"name":"test","domain_id":"MLM-PERFUMES","attributes":[]}),
]
for path, body in attempts:
  r=requests.post(f"{API}{path}",headers=H,json=body,timeout=10)
  print(f"POST {path} -> {r.status_code}: {r.text[:300]}")

# Get current CPID's full data
CPID="MLM48919985"
r=requests.get(f"{API}/products/{CPID}",headers=H,timeout=10).json()
print(f"\n=== CPID {CPID} full data ===")
print(f"name: {r.get('name')}")
print(f"pdp_types: {r.get('pdp_types')}")
print(f"status: {r.get('status')}")
print(f"domain_id: {r.get('domain_id')}")
print(f"category_id: {r.get('category_id')}")
print(f"buy_box_winner: {r.get('buy_box_winner')}")
print("attributes:")
for a in r.get("attributes",[])[:15]:
  print(f"  {a.get('id')}: {a.get('value_name')}")
print(f"creator_id: {r.get('creator_id')}")
print(f"pdp_url: {r.get('settings',{}).get('pdp_url')}")
print(f"family_name: {r.get('family_name')}")
