import os, requests, base64, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
ITEM="MLM5510147104"

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
print(f"[BEFORE] status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")

if g.get("status")=="active":
  rp=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"paused"},timeout=15)
  print(f"[PAUSE] HTTP {rp.status_code}")

rc=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"closed"},timeout=15)
print(f"[CLOSE] HTTP {rc.status_code}: {rc.text[:200]}")

# Try DELETE (usually unsupported on MX but harmless)
rd=requests.delete(f"{API}/items/{ITEM}",headers=H,timeout=15)
print(f"[DELETE attempt] HTTP {rd.status_code}")

# Supabase: blacklist in no_replenish + directive
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json",
     "Prefer":"return=representation,resolution=merge-duplicates"}
rn=requests.post(f"{SB}/rest/v1/meli_no_replenish_items",headers=SBH,
  json={"item_id":ITEM,"account":"AH","reason":"user: eliminar listing"},timeout=12)
print(f"[no_replenish_items] HTTP {rn.status_code}")
rd2=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
  json={"account":"AH","scope":"item","scope_value":ITEM,"directive_type":"closed",
        "raw_user_message":"elimina esta publicacion de adrian 5510147104"},timeout=12)
print(f"[directive closed] HTTP {rd2.status_code}")

# Verify
g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12)
print(f"[VERIFY] HTTP {g2.status_code} status={g2.json().get('status') if g2.status_code==200 else 'gone'}")

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
