import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

RT_A=os.environ["MELI_REFRESH_TOKEN_AH"]
ra=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_A},timeout=20)
AT_A=ra.json()["access_token"]; HA={"Authorization":f"Bearer {AT_A}"}

RT_M=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
rm=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_M},timeout=20)
AT_M=rm.json()["access_token"]
HM={"Authorization":f"Bearer {AT_M}"}; HJM={**HM,"Content-Type":"application/json"}

SRC="MLM2976325463"
src=requests.get(f"{API}/items/{SRC}",headers=HA,timeout=15).json()

# Dump SIZE_GRID_ID + variation structure
print("=== SOURCE FASHION ATTRS ===")
for a in src.get("attributes",[]):
  if "GRID" in (a.get("id") or "") or "SIZE" in (a.get("id") or ""):
    print(f"  {a.get('id')} = {a.get('value_name')} (value_id={a.get('value_id')})")

print("\n=== SOURCE VARIATIONS ===")
for v in src.get("variations",[]):
  print(f"  variation_id={v.get('id')}")
  for ac in v.get("attribute_combinations",[]):
    print(f"    attr {ac.get('id')}={ac.get('value_name')} (value_id={ac.get('value_id')})")
  for ac in v.get("attributes",[]) or []:
    print(f"    extra attr {ac.get('id')}={ac.get('value_name')}")

# Get pics from prev upload (already uploaded)
PICS=["843389-MLM112420198538_062026","853216-MLM113582132069_062026","692677-MLM113582132089_062026","846114-MLM113581959235_062026","958878-MLM112420024468_062026","644308-MLM112420308530_062026","885995-MLM113582132141_062026","909513-MLM112420024518_062026","835666-MLM112419905686_062026","821832-MLM112420024554_062026"]

# Get desc
dr=requests.get(f"{API}/items/{SRC}/description",headers=HA,timeout=15)
desc=dr.json().get("plain_text","") if dr.status_code==200 else ""

# Get SIZE_GRID_ID and any fashion grid required
size_grid_id=None
size_grid_row_id=None
for a in src.get("attributes",[]):
  if a.get("id")=="SIZE_GRID_ID":
    size_grid_id=a.get("value_id") or a.get("value_name")
  if a.get("id")=="SIZE_GRID_ROW_ID":
    size_grid_row_id=a.get("value_id") or a.get("value_name")

# Build variations preserving exact structure
variations=[]
for v in src.get("variations",[]):
  combo=[]
  for ac in v.get("attribute_combinations",[]):
    e={"id":ac.get("id")}
    if ac.get("value_id"): e["value_id"]=ac.get("value_id")
    if ac.get("value_name"): e["value_name"]=ac.get("value_name")
    combo.append(e)
  v_attrs=[]
  for ac in v.get("attributes",[]) or []:
    e={"id":ac.get("id")}
    if ac.get("value_id"): e["value_id"]=ac.get("value_id")
    if ac.get("value_name"): e["value_name"]=ac.get("value_name")
    v_attrs.append(e)
  variations.append({
    "attribute_combinations": combo,
    "attributes": v_attrs,
    "available_quantity": v.get("available_quantity") or 10,
    "price": v.get("price") or src.get("price"),
    "picture_ids": PICS[:3]
  })

# Top-level attrs (incluir SIZE_GRID_ID)
keep={"BRAND","GENDER","MAIN_MATERIAL","UNITS_PER_PACK","ITEM_CONDITION","MODEL","LINE","CLOTHING_TYPE","UNDERWEAR_TYPE","PATTERN","DESIGN","SIZE_GRID_ID","SIZE_GRID_ROW_ID","MAIN_COLOR","COLOR"}
attrs=[]
for a in src.get("attributes",[]):
  aid=a.get("id")
  if aid in keep and aid!="SIZE":
    e={"id":aid}
    if a.get("value_id"): e["value_id"]=a.get("value_id")
    if a.get("value_name"): e["value_name"]=a.get("value_name")
    attrs.append(e)

print(f"\nsize_grid_id: {size_grid_id}")
print(f"sending {len(attrs)} attrs + {len(variations)} variations")

payload={
  "title": src.get("title"),
  "category_id": src.get("category_id"),
  "price": src.get("price") or 399,
  "currency_id":"MXN",
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in PICS],
  "attributes": attrs,
  "variations": variations,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc[:5000]}
}

p=requests.post(f"{API}/items",headers=HJM,json=payload,timeout=30)
print(f"\nPOST: {p.status_code}")
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJM,json={"plain_text":desc[:5000]},timeout=20)
  print(f"\n✅ CLONED to Mayrely: {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
