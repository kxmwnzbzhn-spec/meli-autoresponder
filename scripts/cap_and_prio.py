import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
ITEM="MLM2976325463"

r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
vars_list=g.get("variations") or []
print(f"[before]")
for v in vars_list:
  sz="?"
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE": sz=ac.get("value_name")
  print(f"  id={v.get('id')} size={sz} qty={v.get('available_quantity')}")

# PUT: per-variant qty=1
v_updates=[{"id":v.get("id"),"available_quantity":1} for v in vars_list]
payload={"status":"active","variations":v_updates}
pu=requests.put(f"{API}/items/{ITEM}",headers=H,json=payload,timeout=20)
print(f"[PUT qty=1] HTTP {pu.status_code}")
if pu.status_code>=300: print(f"  body: {pu.text[:600]}")

# Verify
g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
print(f"\n[after]")
for v in g2.get('variations',[]):
  sz="?"
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE": sz=ac.get("value_name")
  print(f"  id={v.get('id')} size={sz} qty={v.get('available_quantity')}")

# Supabase
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json",
     "Prefer":"return=representation,resolution=merge-duplicates"}

row={"item_id":ITEM,"account":"AH","default_qty":1,"product_name":g.get("title")}
rp=requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,json=row,timeout=12)
print(f"\n[priority_replenish] HTTP {rp.status_code}: {rp.text[:200]}")

d={"account":"AH","scope":"item","scope_value":ITEM,
   "directive_type":"priority_replenish","value_numeric":1,
   "raw_user_message":"cada variante 1 visible, auto repone 30s"}
rd=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,json=d,timeout=12)
print(f"[directive] HTTP {rd.status_code}")

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
