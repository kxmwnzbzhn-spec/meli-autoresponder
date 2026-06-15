import os, requests, json, time, base64
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

ALREADY_DONE = {"MLM63875183"}
GROUP_CAT_499_599 = []  # already done
GROUP_TRAD_599_999 = ["MLM48244979","MLM64288232","MLM44714337","MLM35713227","MLM37110751","MLM52667244","MLM44714150","MLM47219000","MLM44712057","MLM58616124"]
GROUP_TRAD_399_499 = ["MLM44709174","MLM35886513","MLM58788792","MLM58918178"]

DOMAIN_CAT_MAP = {
  "MLM-SPEAKERS": "MLM59800",
  "MLM-HEADPHONES": "MLM2107",
  "MLM-PERFUMES": "MLM1271",
}

def get_cpid(cpid):
  try:
    r=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15)
    if r.status_code==200: return r.json()
  except: pass
  return None

def resolve_category(cp):
  cat=cp.get("category_id") if cp else None
  if cat: return cat
  dom=cp.get("domain_id") if cp else None
  if dom and dom in DOMAIN_CAT_MAP: return DOMAIN_CAT_MAP[dom]
  return None

def set_bounds(cpid, item_id, floor, ceiling):
  raw=f"item bounds floor={floor} ceiling={ceiling}"
  for dt,val in [("set_floor",floor),("set_ceiling",ceiling)]:
    try:
      requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":"AH","scope":"catalog_product_id" if cpid else "item",
              "scope_value":cpid or item_id,"directive_type":dt,
              "value_numeric":val,"raw_user_message":raw},timeout=10)
    except: pass

def setup_replenish(item_id, name):
  try:
    requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
      json={"item_id":item_id,"account":"AH","default_qty":1,"product_name":(name or "")[:200]},timeout=10)
  except: pass

def publish_catalog(cpid, low, high):
  cp=get_cpid(cpid)
  if not cp: print(f"  ❌ no CPID {cpid}"); return None
  cat=resolve_category(cp)
  if not cat: print(f"  ❌ no category for {cpid} (domain={cp.get('domain_id')})"); return None
  body={
    "title":(cp.get("name") or "")[:60],
    "catalog_product_id":cpid,
    "category_id":cat,
    "price":high,"currency_id":"MXN","available_quantity":1,
    "buying_mode":"buy_it_now","condition":"new",
    "listing_type_id":"gold_pro","catalog_listing":True,
    "channels":["marketplace"],
  }
  v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
  if v.status_code>=300:
    try:
      j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
      if err: print(f"  ❌ VALIDATE {cpid}: {json.dumps(err)[:400]}"); return None
    except: pass
  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  if p.status_code>=300: print(f"  ❌ POST {cpid}: {p.text[:400]}"); return None
  out=p.json(); iid=out["id"]
  print(f"  ✅ CATALOG {iid} ${high} bounds[{low},{high}] | https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}-_JM")
  set_bounds(cpid, iid, low, high); setup_replenish(iid, cp.get("name"))
  return iid

def publish_tradicional(cpid, low, high):
  """Use catalog_product_id + gold_special — MELI auto-fills attrs and GTIN."""
  cp=get_cpid(cpid)
  if not cp: print(f"  ❌ no CPID {cpid}"); return None
  cat=resolve_category(cp)
  if not cat: print(f"  ❌ no category for {cpid}"); return None
  pics=[{"source":p["url"]} for p in (cp.get("pictures") or [])][:10]
  body={
    "title":(cp.get("name") or "")[:60],
    "catalog_product_id":cpid,
    "category_id":cat,
    "price":high,"currency_id":"MXN","available_quantity":1,
    "buying_mode":"buy_it_now","condition":"new",
    "listing_type_id":"gold_special",
    "pictures":pics,
  }
  v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
  if v.status_code>=300:
    try:
      j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
      if err: print(f"  ❌ VALIDATE {cpid}: {json.dumps(err)[:400]}"); return None
    except: pass
  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  if p.status_code>=300: print(f"  ❌ POST {cpid}: {p.text[:400]}"); return None
  out=p.json(); iid=out["id"]
  print(f"  ✅ TRAD-linked {iid} ${high} bounds[{low},{high}] | https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}-_JM")
  set_bounds(cpid, iid, low, high); setup_replenish(iid, cp.get("name"))
  return iid

print("\n=== GROUP 1: CATALOGO [$499 - $599] ===")
for cpid in GROUP_CAT_499_599:
  if cpid in ALREADY_DONE: continue
  print(f"\n--- {cpid} ---")
  publish_catalog(cpid, 499, 599)

print("\n=== GROUP 2: TRADICIONAL-linked [$599 - $999] ===")
for cpid in GROUP_TRAD_599_999:
  if cpid in ALREADY_DONE: continue
  print(f"\n--- {cpid} ---")
  publish_tradicional(cpid, 599, 999)

print("\n=== GROUP 3: TRADICIONAL-linked [$399 - $499] ===")
for cpid in GROUP_TRAD_399_499:
  if cpid in ALREADY_DONE: continue
  print(f"\n--- {cpid} ---")
  publish_tradicional(cpid, 399, 499)

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
