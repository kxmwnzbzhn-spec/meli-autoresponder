import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CPID="MLM48919985"
PRICE=199

for a in range(5):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED ASVA] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"[CPID] name={cp.get('name')}")
print(f"  domain={cp.get('domain_id')} category={cp.get('category_id')}")

# Resolve category
DOMAIN_CAT_MAP={
  "MLM-SPEAKERS":"MLM59800","MLM-HEADPHONES":"MLM2107","MLM-PERFUMES":"MLM1271",
}
cat=cp.get("category_id")
if not cat:
  cat=DOMAIN_CAT_MAP.get(cp.get("domain_id"))
print(f"[CAT] {cat}")

if not cat:
  print("❌ no category"); raise SystemExit(1)

body={
  "title":(cp.get("name") or "")[:60],
  "catalog_product_id":CPID,
  "category_id":cat,
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "condition":"new",
  "listing_type_id":"gold_pro",
  "catalog_listing":True,
  "channels":["marketplace"],
}

v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
print(f"[VALIDATE] HTTP {v.status_code}")
if v.status_code>=300:
  try:
    j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
    if err: print(f"  ERR: {json.dumps(err,ensure_ascii=False)[:600]}"); raise SystemExit(1)
  except SystemExit: raise
  except: pass

p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
print(f"[POST] HTTP {p.status_code}")
if p.status_code>=300:
  print(f"  body: {p.text[:800]}"); raise SystemExit(1)
out=p.json(); NEW_ID=out["id"]
print(f"✅ {NEW_ID} ${PRICE} | https://articulo.mercadolibre.com.mx/{NEW_ID.replace('MLM','MLM-')}-_JM")

# Supabase: bounds + priority replenish
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation,resolution=merge-duplicates"}
for dt,val in [("set_floor",PRICE),("set_ceiling",PRICE)]:
  requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"ASVA","scope":"catalog_product_id","scope_value":CPID,
          "directive_type":dt,"value_numeric":val,
          "raw_user_message":f"publica catalogo asva precio ${PRICE}"},timeout=10)
rp=requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
  json={"item_id":NEW_ID,"account":"ASVA","default_qty":1,"product_name":cp.get("name")},timeout=10)
print(f"[priority_replenish] HTTP {rp.status_code}")

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
  requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_ASVA",
    headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
