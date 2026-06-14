import os, requests, base64
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token",
  "client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20)
print(f"HTTP {r.status_code}")
if r.status_code>=300:
  print(r.text[:400]); raise SystemExit(1)
tk=r.json(); NEW_RT=tk["refresh_token"]; AT=tk["access_token"]
print(f"FRESH_AH_REFRESH_TOKEN={NEW_RT}")
# Verify by /users/me
me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
print(f"verify seller_id={me.get('id')} nick={me.get('nickname')}")

# Sync to GH secret
import nacl.encoding, nacl.public
GHT=os.environ["GH_PAT"]
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
R="kxmwnzbzhn-spec/meli-autoresponder"
pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
enc=base64.b64encode(sealed).decode()
ru=requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_AH",
  headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
print(f"GH_SECRET_SYNC HTTP {ru.status_code}")
