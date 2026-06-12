import os, requests, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
ITEM="MLM5496444002"

ACCS=[
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("MAYRELY","MELI_REFRESH_TOKEN_MAYRELY"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
  ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
  ("YC_NEW","MELI_REFRESH_TOKEN"),
]

owner=None; AT=None; META=None; NEW_RT=None; ENV=None
for nick,sec in ACCS:
  rt=os.environ.get(sec)
  if not rt: continue
  try:
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
      "client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
    if r.status_code>=300: continue
    tk=r.json(); at=tk["access_token"]; nrt=tk["refresh_token"]
    h={"Authorization":f"Bearer {at}"}
    g=requests.get(f"{API}/items/{ITEM}",headers=h,timeout=10).json()
    if g.get("id")!=ITEM: continue
    me=requests.get(f"{API}/users/me",headers=h,timeout=8).json()
    if me.get("id")==g.get("seller_id"):
      owner=nick; AT=at; META=g; NEW_RT=nrt; ENV=sec
      print(f">>> OWNER={nick} | seller={me.get('id')} | new_rt={nrt}")
      break
  except Exception as e:
    print(f"{nick}: err {e}"); continue

if not owner:
  print(f"NOT FOUND owner for {ITEM}"); raise SystemExit(1)

H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
print(f"[ITEM] status={META.get('status')} sub={META.get('sub_status')} qty={META.get('available_quantity')} price={META.get('price')}")
print(f"  title={META.get('title')}")

# Close (status=closed). For paused items first activate? No — closed works from any active state.
# If active, set paused first then closed
if META.get("status")=="active":
  rp=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"paused"},timeout=15)
  print(f"[PAUSE] HTTP {rp.status_code}: {rp.text[:200]}")
rc=requests.put(f"{API}/items/{ITEM}",headers=H,json={"status":"closed"},timeout=15)
print(f"[CLOSE] HTTP {rc.status_code}: {rc.text[:200]}")

# Optional DELETE (only works on closed items)
rd=requests.delete(f"{API}/items/{ITEM}",headers=H,timeout=15)
print(f"[DELETE attempt] HTTP {rd.status_code}: {rd.text[:200]}")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10)
print(f"[VERIFY] HTTP {g2.status_code} status={g2.json().get('status') if g2.status_code==200 else 'gone'}")

# Sync rotated RT
try:
  import nacl.encoding, nacl.public
except Exception:
  os.system("pip install pynacl -q")
  import nacl.encoding, nacl.public
GHT=os.environ.get("GH_PAT")
if GHT and NEW_RT and ENV:
  GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
  R="kxmwnzbzhn-spec/meli-autoresponder"
  pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
  pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
  sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
  enc=base64.b64encode(sealed).decode()
  ru=requests.put(f"https://api.github.com/repos/{R}/actions/secrets/{ENV}",headers=GHH,
    json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
  print(f"[GH SECRET UPDATE {ENV}] HTTP {ru.status_code}")
