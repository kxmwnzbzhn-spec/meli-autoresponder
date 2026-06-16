import os, requests, base64, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
ITEM="MLM2943277465"

r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
print(f"[BEFORE] status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
print(f"  title={g.get('title')[:80]}")

rp=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"paused","available_quantity":0},timeout=15)
print(f"[PAUSE+qty=0] HTTP {rp.status_code}")

SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation,resolution=merge-duplicates"}

raw="pausa esto en asva 2943277465"
for dt in ["pause","no_replenish","lock_from_war"]:
  rd=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"ASVA","scope":"item","scope_value":ITEM,"directive_type":dt,"raw_user_message":raw},timeout=10)
  print(f"  [directive {dt}] HTTP {rd.status_code}")

rn=requests.post(f"{SB}/rest/v1/meli_no_replenish_items",headers=SBH,
  json={"item_id":ITEM,"account":"ASVA","reason":"user: pausa manual"},timeout=10)
print(f"[no_replenish] HTTP {rn.status_code}")

g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
print(f"[AFTER] status={g2.get('status')} qty={g2.get('available_quantity')}")

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
  print("[RT sync ASVA] done")
