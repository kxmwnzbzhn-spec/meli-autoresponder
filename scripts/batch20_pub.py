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
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation,resolution=merge-duplicates"}

# CPID groups — SKIP already-published: MLM63875183 (TRAD)
ALREADY_DONE = {"MLM63875183"}
GROUP_CAT_499_599 = ["MLM61262890","MLM54696427","MLM37361021","MLM70607552","MLM37918100"]
GROUP_TRAD_599_999 = ["MLM48244979","MLM64288232","MLM44714337","MLM35713227","MLM37110751","MLM52667244","MLM44714150","MLM47219000","MLM44712057","MLM58616124"]
GROUP_TRAD_399_499 = ["MLM44709174","MLM35886513","MLM58788792","MLM58918178"]

def get_cpid(cpid):
  try:
    r=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15)
    if r.status_code==200: return r.json()
  except: pass
  return None

def get_competitors(cpid, limit=10):
  """Get list of items competing on CPID — they tell us category + GTIN."""
  try:
    r=requests.get(f"{API}/products/{cpid}/items?limit={limit}",headers=H,timeout=15)
    if r.status_code==200: return r.json().get("results",[])
  except: pass
  return []

def get_item_meta(iid):
  try:
    r=requests.get(f"{API}/items/{iid}",headers=H,timeout=12)
    if r.status_code==200: return r.json()
  except: pass
  return None

def derive_category_gtin(cpid):
  """Fetch category_id and GTIN from real competing items."""
  cat=None; gtin=None
  comps=get_competitors(cpid, limit=20)
  for c in comps:
    iid=c.get("item_id") or c.get("id")
    if not iid: continue
    m=get_item_meta(iid)
    if not m: continue
    if not cat: cat=m.get("category_id")
    if not gtin:
      for a in m.get("attributes",[]):
        if a.get("id")=="GTIN" and a.get("value_name"):
          gtin=a.get("value_name"); break
    if cat and gtin: break
  return cat, gtin

def set_bounds(cpid, item_id, floor, ceiling):
  raw=f"item bounds floor={floor} ceiling={ceiling}"
  for dt,val in [("set_floor",floor),("set_ceiling",ceiling)]:
    try:
      requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":"AH","scope":"catalog_product_id" if cpid else "item",
              "scope_value":cpid or item_id,
              "directive_type":dt,"value_numeric":val,"raw_user_message":raw},timeout=10)
    except: pass

def setup_replenish(item_id, name):
  try:
    requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
      json={"item_id":item_id,"account":"AH","default_qty":1,"product_name":(name or "")[:200]},timeout=10)
  except: pass

def publish_catalog(cpid, low, high):
  cp=get_cpid(cpid)
  cat=cp.get("category_id") if cp else None
  if not cat:
    cat,_=derive_category_gtin(cpid)
  if not cat:
    print(f"  ❌ no category for {cpid}"); return None
  body={
    "title":(cp.get("name") or "")[:60] if cp else "Product",
    "catalog_product_id":cpid,
    "category_id":cat,
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
      if err: print(f"  ❌ VALIDATE {cpid}: {json.dumps(err)[:400]}"); return None
    except: pass
  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  if p.status_code>=300:
    print(f"  ❌ POST {cpid}: {p.text[:400]}"); return None
  out=p.json(); iid=out["id"]
  print(f"  ✅ CATALOG {iid} ${high} bounds[{low},{high}] | https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}-_JM")
  set_bounds(cpid, iid, low, high); setup_replenish(iid, cp.get("name") if cp else "")
  return iid

def publish_tradicional(cpid, low, high):
  cp=get_cpid(cpid)
  if not cp: print(f"  ❌ no CPID {cpid}"); return None
  name=cp.get("name") or ""
  pics=[{"source":p["url"]} for p in (cp.get("pictures") or [])][:10]
  attrs=cp.get("attributes") or []
  cat=cp.get("category_id")
  # Get competitor for category + GTIN
  comp_cat, comp_gtin = derive_category_gtin(cpid)
  cat=cat or comp_cat
  if not cat:
    print(f"  ❌ no category for {cpid}"); return None

  ATTRS=[]
  for a in attrs:
    if a.get("id") in ("BRAND","MODEL","COLOR","GTIN","LINE","PERFUME_NAME","PERFUME_TYPE",
                       "UNIT_VOLUME","GENDER","MAIN_MATERIAL","COMPOSITION","UNITS_PER_PACK","AGE_GROUP"):
      ATTRS.append({"id":a["id"],"value_name":a.get("value_name")})
  has_gtin=any(a["id"]=="GTIN" for a in ATTRS)
  if not has_gtin and comp_gtin:
    ATTRS.append({"id":"GTIN","value_name":comp_gtin})
    has_gtin=True
  if not any(a["id"]=="BRAND" for a in ATTRS):
    ATTRS.append({"id":"BRAND","value_name":"Genérico"})
  if not any(a["id"]=="ITEM_CONDITION" for a in ATTRS):
    ATTRS.append({"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"})

  body={
    "title":name[:60],
    "category_id":cat,
    "price":high,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":pics,
    "attributes":ATTRS,
  }

  for attempt in range(3):
    v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
    if v.status_code<300: break
    try:
      j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
      codes=[c.get("code") for c in err]
      if "item.attribute.missing_conditional_required" in codes and not has_gtin:
        ATTRS.append({"id":"EMPTY_GTIN_REASON","value_name":"El producto no tiene código registrado"})
        body["attributes"]=ATTRS; continue
      if "item.title.length.invalid" in codes:
        body["title"]=body["title"][:58]; continue
      print(f"  ❌ VALIDATE {cpid}: {json.dumps(err)[:500]}"); return None
    except: print(f"  ❌ {v.text[:300]}"); return None

  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  if p.status_code>=300:
    print(f"  ❌ POST {cpid}: {p.text[:400]}"); return None
  out=p.json(); iid=out["id"]
  print(f"  ✅ TRAD {iid} ${high} bounds[{low},{high}] | https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}-_JM")
  set_bounds(cpid, iid, low, high); setup_replenish(iid, name)
  return iid

print("\n=== GROUP 1: CATALOGO [$499 - $599] ===")
for cpid in GROUP_CAT_499_599:
  if cpid in ALREADY_DONE: continue
  print(f"\n--- {cpid} ---")
  publish_catalog(cpid, 499, 599)

print("\n=== GROUP 2: TRADICIONAL [$599 - $999] ===")
for cpid in GROUP_TRAD_599_999:
  if cpid in ALREADY_DONE: continue
  print(f"\n--- {cpid} ---")
  publish_tradicional(cpid, 599, 999)

print("\n=== GROUP 3: TRADICIONAL [$399 - $499] ===")
for cpid in GROUP_TRAD_399_499:
  if cpid in ALREADY_DONE: continue
  print(f"\n--- {cpid} ---")
  publish_tradicional(cpid, 399, 499)

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
