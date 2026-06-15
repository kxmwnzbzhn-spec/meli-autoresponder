import os, requests, json, time, base64, sys
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]

for a in range(5):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json",
     "Prefer":"return=representation,resolution=merge-duplicates"}

# 3 groups
GROUP_CAT_499_599 = ["MLM61262890","MLM54696427","MLM37361021","MLM70607552","MLM37918100"]
GROUP_TRAD_599_999 = ["MLM48244979","MLM63875183","MLM64288232","MLM44714337","MLM35713227","MLM37110751","MLM52667244","MLM44714150","MLM47219000","MLM44712057","MLM58616124"]
GROUP_TRAD_399_499 = ["MLM44709174","MLM35886513","MLM58788792","MLM58918178"]

def safe_get_cpid(cpid):
  for _ in range(3):
    try:
      r=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15)
      if r.status_code==200: return r.json()
      if r.status_code>=400 and r.status_code<500: return None
    except: pass
    time.sleep(2)
  return None

def predict_category(title, brand):
  qs=requests.utils.quote(f"{brand} {title}")
  try:
    dd=requests.get(f"{API}/sites/MLM/domain_discovery/search?limit=3&q={qs}",headers=H,timeout=10)
    if dd.status_code==200:
      arr=dd.json()
      if isinstance(arr,list) and arr: return arr[0].get("category_id")
  except: pass
  return None

def setup_replenish(item_id, name):
  try:
    r=requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
      json={"item_id":item_id,"account":"AH","default_qty":1,"product_name":name},timeout=10)
    return r.status_code<300
  except: return False

def set_bounds(cpid, item_id, floor, ceiling):
  raw=f"item bounds floor={floor} ceiling={ceiling}"
  for dt,val in [("set_floor",floor),("set_ceiling",ceiling)]:
    try:
      requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":"AH","scope":"catalog_product_id" if cpid else "item",
              "scope_value":cpid or item_id,
              "directive_type":dt,"value_numeric":val,"raw_user_message":raw},timeout=10)
    except: pass

def publish_catalog(cpid, low, high):
  cp=safe_get_cpid(cpid)
  if not cp:
    print(f"  ❌ CPID {cpid} not found"); return None
  body={
    "title":(cp.get("name") or "")[:60],
    "catalog_product_id":cpid,
    "category_id":cp.get("category_id"),
    "price":high,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_pro",
    "catalog_listing":True,
    "channels":["marketplace"],
  }
  v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
  if v.status_code>=300:
    try:
      j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
      if err: print(f"  ❌ VALIDATE: {json.dumps(err)[:300]}"); return None
    except: pass
  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  if p.status_code>=300:
    print(f"  ❌ POST {p.status_code}: {p.text[:300]}"); return None
  out=p.json(); iid=out["id"]
  print(f"  ✅ CATALOG {iid} ${high} bounds[{low},{high}] | https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}-_JM")
  set_bounds(cpid, iid, low, high)
  setup_replenish(iid, cp.get("name"))
  return iid

def publish_tradicional(cpid, low, high):
  cp=safe_get_cpid(cpid)
  if not cp:
    print(f"  ❌ CPID {cpid} not found"); return None
  name=cp.get("name") or ""
  pics=[{"source":p["url"]} for p in (cp.get("pictures") or [])][:10]
  attrs=cp.get("attributes") or []
  brand_attr=next((a for a in attrs if a.get("id")=="BRAND"),{})
  brand=brand_attr.get("value_name","Genérico")
  
  # Find category
  cat_id=cp.get("category_id")
  if not cat_id:
    cat_id=predict_category(name, brand)
  if not cat_id:
    print(f"  ❌ no category for {cpid}"); return None
  
  # Build attributes (copy from CPID, sanitize)
  ATTRS=[]
  for a in attrs:
    if a.get("id") in ("BRAND","MODEL","COLOR","GTIN","LINE","PERFUME_NAME","PERFUME_TYPE",
                       "UNIT_VOLUME","GENDER","MAIN_MATERIAL","COMPOSITION","UNITS_PER_PACK",
                       "AGE_GROUP","SIZE_GRID_ID"):
      ATTRS.append({"id":a["id"],"value_name":a.get("value_name")})
  has_brand=any(a["id"]=="BRAND" for a in ATTRS)
  if not has_brand: ATTRS.append({"id":"BRAND","value_name":brand})
  if not any(a["id"]=="ITEM_CONDITION" for a in ATTRS):
    ATTRS.append({"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"})
  
  body={
    "title":name[:60],
    "category_id":cat_id,
    "price":high,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":pics,
    "attributes":ATTRS,
  }
  
  # try
  for attempt in range(2):
    v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
    if v.status_code>=300:
      try:
        j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
        if err:
          # If GTIN required and missing, add EMPTY_GTIN_REASON
          codes=[c.get("code") for c in err]
          if "item.attribute.missing_conditional_required" in codes and not any(a["id"]=="EMPTY_GTIN_REASON" for a in ATTRS) and not any(a["id"]=="GTIN" for a in ATTRS):
            ATTRS.append({"id":"EMPTY_GTIN_REASON","value_name":"El producto no tiene código registrado"})
            body["attributes"]=ATTRS
            continue
          # If title too long
          if "item.title.length.invalid" in codes:
            body["title"]=body["title"][:58]
            continue
          print(f"  ❌ VALIDATE {cpid}: {json.dumps(err)[:300]}"); return None
      except: pass
    break
  
  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  if p.status_code>=300:
    print(f"  ❌ POST {cpid}: {p.text[:300]}"); return None
  out=p.json(); iid=out["id"]
  print(f"  ✅ TRAD {iid} ${high} bounds[{low},{high}] | https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}-_JM")
  set_bounds(cpid, iid, low, high)
  setup_replenish(iid, name)
  return iid

results=[]
print("\n=== GROUP 1: CATALOGO [$499 - $599] ===")
for cpid in GROUP_CAT_499_599:
  print(f"\n--- {cpid} ---")
  r=publish_catalog(cpid, 499, 599)
  results.append({"cpid":cpid,"group":"CATALOG","item":r})

print("\n=== GROUP 2: TRADICIONAL [$599 - $999] ===")
for cpid in GROUP_TRAD_599_999:
  print(f"\n--- {cpid} ---")
  r=publish_tradicional(cpid, 599, 999)
  results.append({"cpid":cpid,"group":"TRAD","item":r})

print("\n=== GROUP 3: TRADICIONAL [$399 - $499] ===")
for cpid in GROUP_TRAD_399_499:
  print(f"\n--- {cpid} ---")
  r=publish_tradicional(cpid, 399, 499)
  results.append({"cpid":cpid,"group":"TRAD","item":r})

ok=[r for r in results if r["item"]]
fail=[r for r in results if not r["item"]]
print(f"\n=== SUMMARY ===\nOK: {len(ok)}/{len(results)}")
for r in fail: print(f"  FAIL: {r['cpid']} ({r['group']})")

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
