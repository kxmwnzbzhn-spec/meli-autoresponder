import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT CLB] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]; print(f"seller={UID}")

# Look up category attributes / domain for chart creation
cat_attrs=requests.get(f"{API}/categories/MLM194115/attributes",headers=H,timeout=15).json()
domain_id=None
for a in cat_attrs:
  if a.get("id")=="SIZE_GRID_ID":
    print(f"SIZE_GRID_ID attr: {a.get('hierarchy')}")
    for tag in (a.get("tags") or {}):
      print(f"  tag: {tag}")

# Create chart
chart_body={
  "domain_id":"MLM-MEN_UNDERWEAR_AND_PAJAMAS",
  "site_id":"MLM",
  "names":{"main":"CK Pack 3 Tallas SML"},
  "attributes":[
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"AGE_GROUP","value_name":"Adultos"},
  ],
  "rows":[
    {"attributes":[{"id":"SIZE","value_name":"S"},
                   {"id":"WAIST_CIRCUMFERENCE","value_name":"71-76 cm"},
                   {"id":"HIP_CIRCUMFERENCE","value_name":"86-91 cm"}]},
    {"attributes":[{"id":"SIZE","value_name":"M"},
                   {"id":"WAIST_CIRCUMFERENCE","value_name":"81-86 cm"},
                   {"id":"HIP_CIRCUMFERENCE","value_name":"94-99 cm"}]},
    {"attributes":[{"id":"SIZE","value_name":"L"},
                   {"id":"WAIST_CIRCUMFERENCE","value_name":"91-97 cm"},
                   {"id":"HIP_CIRCUMFERENCE","value_name":"102-107 cm"}]},
  ]
}
print("\n--- POST /catalog/charts ---")
rc=requests.post(f"{API}/catalog/charts",headers=H,json=chart_body,timeout=20)
print(f"HTTP {rc.status_code}")
print(rc.text[:1500])

# Alternative endpoint version
print("\n--- POST /catalog/charts/charts ---")
rc2=requests.post(f"{API}/catalog/charts/charts",headers=H,json=chart_body,timeout=20)
print(f"HTTP {rc2.status_code}")
print(rc2.text[:600])

# Try with just SIZE on rows
chart_body2={
  "domain_id":"MLM-MEN_UNDERWEAR_AND_PAJAMAS",
  "site_id":"MLM",
  "names":{"main":"CK SML"},
  "attributes":[],
  "rows":[
    {"attributes":[{"id":"SIZE","value_name":"S"}]},
    {"attributes":[{"id":"SIZE","value_name":"M"}]},
    {"attributes":[{"id":"SIZE","value_name":"L"}]},
  ]
}
print("\n--- POST /catalog/charts (simple) ---")
rc3=requests.post(f"{API}/catalog/charts",headers=H,json=chart_body2,timeout=20)
print(f"HTTP {rc3.status_code}")
print(rc3.text[:1500])

print(f"\nFINAL_ROTATED_TOKENS={json.dumps({'MELI_REFRESH_TOKEN_CLARIBEL':NEW_RT})}")
