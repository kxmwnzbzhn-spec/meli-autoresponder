import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT CLB] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Get category domain
cat=requests.get(f"{API}/categories/MLM194115",headers=H,timeout=15).json()
print(f"[category] {cat.get('name')} | domain_id: {cat.get('domain_id')}")
# Use domain_discovery
dd=requests.get(f"{API}/sites/MLM/domain_discovery/search?limit=3&q=Calvin%20Klein%20Boxers",
  headers=H,timeout=15).json()
print(f"[domain_discovery] {dd[:2] if isinstance(dd,list) else dd}")

# Try several domain formats
domains_to_try=["MLM-UNDERWEARS","MLM-BRIEFS","MLM-UNDERWEAR","MLM-LINGERIE","UNDERWEARS","UNDERWEAR"]
if isinstance(dd,list) and dd:
  d=dd[0].get("domain_id")
  if d and d not in domains_to_try: domains_to_try.insert(0,d)

for dom in domains_to_try:
  body={
    "domain_id":dom,
    "site_id":"MLM",
    "names":{"main":"CK SML"},
    "attributes":[
      {"id":"GENDER","value_name":"Hombre"},
      {"id":"AGE_GROUP","value_name":"Adultos"},
    ],
    "rows":[
      {"attributes":[{"id":"SIZE","value_name":"S"}]},
      {"attributes":[{"id":"SIZE","value_name":"M"}]},
      {"attributes":[{"id":"SIZE","value_name":"L"}]},
    ]
  }
  rc=requests.post(f"{API}/catalog/charts",headers=H,json=body,timeout=20)
  print(f"[domain {dom}] HTTP {rc.status_code}: {rc.text[:250]}")
  if rc.status_code<300:
    print(f"CHART CREATED: {rc.json()}")
    break

print(f"\nFINAL_ROTATED_TOKENS={json.dumps({'MELI_REFRESH_TOKEN_CLARIBEL':NEW_RT})}")
