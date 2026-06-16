import os, requests, base64, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
PRICE=799
ITEMS=["MLM5511173004","MLM5511745190","MLM5511745194","MLM5511745202"]

r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation,resolution=merge-duplicates"}

raw_msg=f"sube a ${PRICE} y NO bajar precio (pin)"
for ITEM in ITEMS:
  print(f"\n--- {ITEM} ---")
  g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
  cpid=g.get("catalog_product_id")
  print(f"  BEFORE: price={g.get('price')} status={g.get('status')} CPID={cpid} | {g.get('title','')[:60]}")
  
  # PUT price + ensure active
  rp=requests.put(f"{API}/items/{ITEM}",headers=H,json={"price":PRICE,"status":"active"},timeout=15)
  print(f"  PUT price=${PRICE}: HTTP {rp.status_code}")
  if rp.status_code>=300: print(f"    body: {rp.text[:200]}")
  
  # Supabase: pin_price + set_floor + set_ceiling directives (per CLAUDE.md PIN rule)
  scope="catalog_product_id" if cpid else "item"
  scope_val=cpid or ITEM
  for dt,val in [("pin_price",PRICE),("set_floor",PRICE),("set_ceiling",PRICE)]:
    rd=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
      json={"account":"AH","scope":scope,"scope_value":scope_val,
            "directive_type":dt,"value_numeric":val,"raw_user_message":raw_msg},timeout=10)
    print(f"  [directive {dt}={val}] HTTP {rd.status_code}")
  
  g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
  print(f"  AFTER: price={g2.get('price')} status={g2.get('status')}")

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
