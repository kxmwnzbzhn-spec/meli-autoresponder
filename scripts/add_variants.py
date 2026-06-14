import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]

r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEM="MLM2976325463"
g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
existing_vars=g.get("variations") or []
print(f"[before] {len(existing_vars)} variations")
existing_sizes=set()
for v in existing_vars:
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id") in ("SIZE","SIZE_GRID_ROW_ID"):
      existing_sizes.add(ac.get("value_name"))
  print(f"  id={v.get('id')} | combos={[(ac.get('id'),ac.get('value_name'),ac.get('value_id')) for ac in v.get('attribute_combinations',[])]} | qty={v.get('available_quantity')}")
print(f"existing sizes: {existing_sizes}")

# EAN per size (from project SKU_Y_EAN.txt)
EAN_BY_SIZE={"S":"2050788300012","M":"2050788300029","L":"2050788300036"}
SKU_PREFIX="CK-PACK3-BRIEF"

# Decide which to add: S, M, L minus existing
all_sizes=["S","M","L"]
missing=[s for s in all_sizes if s not in existing_sizes]
print(f"missing sizes to add: {missing}")
if not missing:
  print("Nothing to add"); raise SystemExit(0)

# Get first variation's structure as template (same picture_ids + ITEM_CONDITION combo + attributes)
template=existing_vars[0]
# Get its attribute_combinations to learn the attribute structure (SIZE_GRID_ROW_ID + value_id mapping)
print(f"\ntemplate variation full combos: {json.dumps(template.get('attribute_combinations',[]),ensure_ascii=False)}")

# Map size -> value_id from SIZE_GRID
# Get the SIZE attribute possible values
cat_attrs=requests.get(f"{API}/categories/MLM194115/attributes",headers=H,timeout=15).json()
SIZE_VALUE_IDS={}
for a in cat_attrs:
  if a.get("id")=="SIZE":
    for v in (a.get("values") or []):
      SIZE_VALUE_IDS[v.get("name")]=v.get("id")
print(f"SIZE value_ids: {SIZE_VALUE_IDS}")

# Build new variations
new_variations=list(existing_vars)
for sz in missing:
  base={
    "price":g.get("price"),
    "available_quantity":1,
    "picture_ids":template.get("picture_ids",[])[:6],
    "attributes":[
      {"id":"SELLER_SKU","value_name":f"{SKU_PREFIX}-{sz}"},
      {"id":"GTIN","value_name":EAN_BY_SIZE[sz]},
    ],
    "attribute_combinations":[],
  }
  # Replicate template's combo structure but swap size
  for ac in template.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      combo={"id":"SIZE","value_name":sz}
      if sz in SIZE_VALUE_IDS:
        combo["value_id"]=SIZE_VALUE_IDS[sz]
      base["attribute_combinations"].append(combo)
    elif ac.get("id")=="SIZE_GRID_ROW_ID":
      # Keep value_id null for new size — let MELI resolve from chart
      base["attribute_combinations"].append({"id":ac.get("id"),"value_name":sz})
    else:
      # Copy as-is
      base["attribute_combinations"].append(ac)
  new_variations.append(base)

print(f"\n[after build] total variations: {len(new_variations)}")

# PUT update
payload={"variations":new_variations}
print(f"\n[PUT payload (truncated)] variations={len(new_variations)} | sizes: {existing_sizes | set(missing)}")
pu=requests.put(f"{API}/items/{ITEM}",headers=H,json=payload,timeout=25)
print(f"[PUT] HTTP {pu.status_code}")
if pu.status_code>=300:
  print(f"  body: {pu.text[:1500]}")
else:
  print(f"  ✅ updated")

# Verify
g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
print(f"\n[after PUT] variations: {len(g2.get('variations') or [])}")
for v in g2.get('variations',[]):
  sz=None
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE": sz=ac.get("value_name")
  print(f"  id={v.get('id')} size={sz} qty={v.get('available_quantity')}")

# Sync RT
try: import nacl.encoding, nacl.public
except: os.system("pip install pynacl -q"); import nacl.encoding, nacl.public
GHT=os.environ.get("GH_PAT")
if GHT and NEW_RT:
  GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
  R="kxmwnzbzhn-spec/meli-autoresponder"
  pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
  pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
  sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
  enc=base64.b64encode(sealed).decode()
  requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_AH",
    headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
