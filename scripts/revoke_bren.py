import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_BREN"]
APP_ID_NEW=os.environ.get("MELI_APP_ID_NEW")

# Get Bren's access token
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
print(f"[oauth] HTTP {r.status_code}")
if r.status_code>=300: print(r.text[:300]); raise SystemExit(1)
tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
print(f"[bren] seller_id={UID} nick={me.get('nickname')}")

# Revoke app authorization - we need to know which app to revoke.
# Try with current MELI_APP_ID (the old app Bren used)
for app in [CID, APP_ID_NEW]:
  if not app: continue
  print(f"\n--- revoke app {app[:4]}***{app[-4:]} for Bren ---")
  rv=requests.delete(f"{API}/users/{UID}/applications/{app}",headers=H,timeout=15)
  print(f"HTTP {rv.status_code}: {rv.text[:300]}")
