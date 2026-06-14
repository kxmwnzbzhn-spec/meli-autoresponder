import os, requests, json, time, base64, sys
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

def get_token(env_var):
  rt=os.environ[env_var]
  for a in range(4):
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
      "client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
    if r.status_code<500: break
    time.sleep(5)
  r.raise_for_status(); t=r.json()
  return t["access_token"], t["refresh_token"]

# 1) Read source from Adrián
AT_AH, NEW_RT_AH = get_token("MELI_REFRESH_TOKEN_AH")
print(f"[ROTATED AH] {NEW_RT_AH}")
H_AH={"Authorization":f"Bearer {AT_AH}"}

SOURCE="MLM2976325463"
src=requests.get(f"{API}/items/{SOURCE}",headers=H_AH,timeout=15).json()
print(f"[src] title={src.get('title')} price={src.get('price')} variations={len(src.get('variations') or [])}")

# Description from source
desc_resp=requests.get(f"{API}/items/{SOURCE}/description",headers=H_AH,timeout=15)
desc_text=""
if desc_resp.status_code==200:
  desc_text=desc_resp.json().get("plain_text","")
print(f"[src desc] {len(desc_text)} chars")

pictures=[{"source": p["secure_url"]} for p in (src.get("pictures") or [])][:12]

# 2) Get token for Claribel
AT_CLB, NEW_RT_CLB = get_token("MELI_REFRESH_TOKEN_CLARIBEL")
print(f"[ROTATED CLARIBEL] {NEW_RT_CLB}")
H_CLB={"Authorization":f"Bearer {AT_CLB}","Content-Type":"application/json"}

# 3) Build payload with 3 size variants (S, M, L)
# Using SIZE_GRID_ID 5915675 (chart_id used previously for CK Boxers)
PRICE = src.get("price") or 399

SKU_PREFIX="CK-PACK3-BRIEF"
EAN_BY_SIZE = {"S":"2050788300012","M":"2050788300029","L":"2050788300036"}

# Try with SIZE attribute (free-text), MELI accepts in this category for non-size_grid sellers
def build_payload(use_size_grid):
  body={
    "title": src.get("title","Calvin Klein Pack 3 Boxers Microfibra Hombre Premium Set 3")[:60],
    "category_id": "MLM194115",
    "price": PRICE,
    "currency_id": "MXN",
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_special",
    "pictures": pictures,
    "attributes": [
      {"id":"BRAND","value_name":"Calvin Klein"},
      {"id":"MODEL","value_name":"Brief"},
      {"id":"COMPOSITION","value_name":"Microfibra"},
      {"id":"MAIN_MATERIAL","value_name":"Microfibra"},
      {"id":"GENDER","value_name":"Hombre"},
      {"id":"FILTRABLE_GENDER","value_name":"Hombre"},
      {"id":"AGE_GROUP","value_name":"Adultos"},
      {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
      {"id":"UNITS_PER_PACK","value_name":"3"},
    ],
    "variations": []
  }
  for sz in ["S","M","L"]:
    var={
      "price": PRICE,
      "available_quantity": 1,
      "attribute_combinations":[],
      "attributes":[
        {"id":"SELLER_SKU","value_name":f"{SKU_PREFIX}-{sz}"},
        {"id":"GTIN","value_name":EAN_BY_SIZE[sz]},
      ],
      "picture_ids":[p["id"] for p in (src.get("pictures") or [])[:6]],
    }
    if use_size_grid:
      var["attribute_combinations"]=[
        {"id":"SIZE","value_name":sz,"values":[{"name":sz}]}
      ]
    else:
      var["attribute_combinations"]=[
        {"id":"SIZE","value_name":sz}
      ]
    body["variations"].append(var)
  if use_size_grid:
    body["attributes"].append({"id":"SIZE_GRID_ID","value_name":"5915675"})
  return body

def try_publish(body, label):
  v=requests.post(f"{API}/items/validate",headers=H_CLB,json=body,timeout=25)
  print(f"[{label} VALIDATE] HTTP {v.status_code}")
  if v.status_code>=300:
    try:
      j=v.json(); causes=j.get("cause",[])
      err=[c for c in causes if c.get("type")=="error"]
      if err:
        print(f"  ERR:",json.dumps(err,ensure_ascii=False)[:1500])
        return None
      print("  warnings only")
    except: print("  raw:",v.text[:800]); return None
  p=requests.post(f"{API}/items",headers=H_CLB,json=body,timeout=30)
  print(f"[{label} POST] HTTP {p.status_code}")
  if p.status_code>=300:
    print(f"  body: {p.text[:1200]}")
    return None
  out=p.json()
  print(f"  ✅ {out['id']} ${out.get('price')} | https://articulo.mercadolibre.com.mx/{out['id'].replace('MLM','MLM-')}-_JM")
  return out

# Try grid first, fallback to free SIZE
out = try_publish(build_payload(True), "WITH SIZE_GRID")
if not out:
  out = try_publish(build_payload(False), "WITHOUT SIZE_GRID")

if not out:
  print("ABORT: both attempts failed")
  raise SystemExit(1)

NEW_ID=out["id"]

# Description
if desc_text:
  rd=requests.post(f"{API}/items/{NEW_ID}/description",headers=H_CLB,
    json={"plain_text":desc_text},timeout=15)
  print(f"[desc] HTTP {rd.status_code}")

# Sync rotated tokens
print(f"\nFINAL_ROTATED_TOKENS={json.dumps({'MELI_REFRESH_TOKEN_AH':NEW_RT_AH,'MELI_REFRESH_TOKEN_CLARIBEL':NEW_RT_CLB})}")
