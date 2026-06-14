import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Get category attributes
a=requests.get(f"{API}/categories/MLM194115/attributes",headers=H,timeout=15).json()
for at in a:
  if at.get("id") in ("SIZE_GRID_ID","SIZE_GRID_ROW_ID","SIZE","MAIN_VARIATION","VARIATION_ATTRIBUTES"):
    print(json.dumps(at,ensure_ascii=False,indent=2)[:2000])
    print("---")

# Try chart create with right URL/format per MELI docs
# Sometimes endpoint is /catalog/charts/charts/{domain_id}
for url in [
  f"{API}/catalog/charts/MLM-UNDERPANTS",
  f"{API}/catalog/charts/MLM/MLM-UNDERPANTS",
  f"{API}/size-charts",
  f"{API}/users/3348766821/catalog/charts",
]:
  body={"site_id":"MLM","names":{"main":"CK SML"},
    "rows":[
      {"attributes":[{"id":"SIZE","value_name":"S"}]},
      {"attributes":[{"id":"SIZE","value_name":"M"}]},
      {"attributes":[{"id":"SIZE","value_name":"L"}]},
    ]}
  r=requests.post(url,headers=H,json=body,timeout=15)
  print(f"\n{url} -> HTTP {r.status_code}: {r.text[:300]}")

# Also try GET on existing CK boxers items by Claribel from any other source to find a public chart
# Look at sellers in same category to find chart_id values
o=requests.get(f"{API}/sites/MLM/search?category=MLM194115&limit=5",headers=H,timeout=15)
print(f"\n[search MLM194115] HTTP {o.status_code}")
if o.status_code==200:
  res=o.json().get("results",[])
  for r2 in res[:5]:
    iid=r2.get("id")
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=8).json()
    for ar in g.get("attributes",[]):
      if ar.get("id")=="SIZE_GRID_ID":
        print(f"  {iid} chart_id={ar.get('value_name')} (seller {g.get('seller_id')})")
        break

print(f"\nFINAL_ROTATED_TOKENS={json.dumps({'MELI_REFRESH_TOKEN_CLARIBEL':NEW_RT})}")
