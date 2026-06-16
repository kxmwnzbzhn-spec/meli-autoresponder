import os, requests, base64, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
ITEM="MLM5511238002"
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=10)
if g.status_code!=200: print(f"GET fail {g.status_code}"); raise SystemExit(1)
gj=g.json()
print(f"[BEFORE] status={gj.get('status')} title={gj.get('title','')[:80]} price={gj.get('price')}")

if gj.get("status")=="active":
  rp=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"paused"},timeout=15)
  print(f"[PAUSE] {rp.status_code}")
rc=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"closed"},timeout=15)
print(f"[CLOSE] {rc.status_code}")

SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation,resolution=merge-duplicates"}
rn=requests.post(f"{SB}/rest/v1/meli_no_replenish_items",headers=SBH,
  json={"item_id":ITEM,"account":"AH","reason":"user: eliminar"},timeout=10)
print(f"[no_replenish] {rn.status_code}")
rd=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
  json={"account":"AH","scope":"item","scope_value":ITEM,"directive_type":"closed",
        "raw_user_message":"elimina esta de adrian 5511238002"},timeout=10)
print(f"[directive] {rd.status_code}")

g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=10)
if g2.status_code==200: print(f"[AFTER] status={g2.json().get('status')}")

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
