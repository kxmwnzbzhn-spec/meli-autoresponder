import os, requests, base64, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

PLAN={
  "MLM2969825393":499,   # Armaf Iconic
  "MLM2969827221":699,   # Luxury Royal Amber
  "MLM2969825239":799,   # Armaf Lions Rugir
}
for IID,PRICE in PLAN.items():
  g=requests.get(f"{API}/items/{IID}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
  print(f"\n--- {IID} ---")
  print(f"  [BEFORE] price={g.get('price')} status={g.get('status')} sub={g.get('sub_status')}")
  # PUT price + status=active (intentar levantar under_review)
  rp=requests.put(f"{API}/items/{IID}",headers=H,json={"price":PRICE,"status":"active","available_quantity":1},timeout=15)
  print(f"  [PUT price=${PRICE} + active] HTTP {rp.status_code}: {rp.text[:200]}")
  g2=requests.get(f"{API}/items/{IID}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
  print(f"  [AFTER] price={g2.get('price')} status={g2.get('status')}")

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
