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
CHART_ID="5915675"

g=requests.get(f"{API}/items/{ITEM}?include_attributes=all",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
existing_vars=g.get("variations") or []
print(f"[before] {len(existing_vars)} variations")
template=existing_vars[0]

# Clean existing variation: strip catalog_product_id + read-only fields
def clean_var(v):
  return {
    "id": v["id"],
    "price": v.get("price"),
    "available_quantity": v.get("available_quantity"),
    "picture_ids": v.get("picture_ids",[]),
    "attribute_combinations": [
      {"id":ac["id"],"value_id":ac.get("value_id"),"value_name":ac.get("value_name")}
      for ac in v.get("attribute_combinations",[])
    ],
    "attributes": [
      {"id":a["id"],"value_name":a.get("value_name")}
      for a in v.get("attributes",[]) if a["id"] in ("GTIN","SELLER_SKU","SIZE_GRID_ROW_ID")
    ],
  }

new_variations=[clean_var(v) for v in existing_vars]

# Standard CK chart row mapping (M=2 confirmed)
ROW_BY_SIZE={"S":"1","M":"2","L":"3"}
SIZE_VALUE_IDS={"S":None,"M":"2282666","L":None}  # leave value_id null for S/L, MELI resolves via chart
EAN_BY_SIZE={"S":"2050788300012","M":"2050788300029","L":"2050788300036"}
SKU_PREFIX="CK-PACK3-BRIEF"

# Find existing sizes
existing_sizes=set()
for v in existing_vars:
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      existing_sizes.add(ac.get("value_name"))
missing=[s for s in ["S","L"] if s not in existing_sizes]
print(f"existing={existing_sizes} missing={missing}")

for sz in missing:
  # Build attribute_combinations replicating template's COLOR + FABRIC_DESIGN + SIZE
  combos=[]
  for ac in template.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      combo={"id":"SIZE","value_name":sz}
      if SIZE_VALUE_IDS.get(sz): combo["value_id"]=SIZE_VALUE_IDS[sz]
      combos.append(combo)
    else:
      combos.append({"id":ac["id"],"value_id":ac.get("value_id"),"value_name":ac.get("value_name")})
  new_var={
    "price": g.get("price"),
    "available_quantity": 1,
    "picture_ids": template.get("picture_ids",[])[:10],
    "attribute_combinations": combos,
    "attributes": [
      {"id":"GTIN","value_name":EAN_BY_SIZE[sz]},
      {"id":"SELLER_SKU","value_name":f"{SKU_PREFIX}-{sz}"},
      {"id":"SIZE_GRID_ROW_ID","value_name":f"{CHART_ID}:{ROW_BY_SIZE[sz]}"},
    ],
  }
  new_variations.append(new_var)

print(f"[total] {len(new_variations)} variations to send")
payload={"variations":new_variations}
pu=requests.put(f"{API}/items/{ITEM}",headers=H,json=payload,timeout=30)
print(f"[PUT] HTTP {pu.status_code}")
if pu.status_code>=300:
  print(f"  body: {pu.text[:1800]}")
else:
  print("  ✅ updated")

g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
print(f"\n[after] {len(g2.get('variations') or [])} variations:")
for v in g2.get('variations',[]):
  sz="?"
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
