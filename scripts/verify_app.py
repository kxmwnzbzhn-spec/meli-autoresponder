import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID_NEW"]; CSEC=os.environ["MELI_APP_SECRET_NEW"]

# client_credentials
r=requests.post(f"{API}/oauth/token",data={"grant_type":"client_credentials","client_id":CID,"client_secret":CSEC},timeout=15)
print(f"[cred] HTTP {r.status_code}")
if r.status_code>=300: print(r.text[:300]); raise SystemExit(1)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Compare CID to expected
EXPECTED="8566085665980242"
print(f"[CID match 8566085665980242?] {CID==EXPECTED}")
print(f"[CID length] {len(CID)}")
print(f"[CID first 4] {CID[:4]}***")
print(f"[CID last 4] ***{CID[-4:]}")

# Get app info
cp=requests.get(f"{API}/applications/{CID}",headers=H,timeout=10).json()
print(f"[app name] {cp.get('name')}")
print(f"[app id from response matches CID?] {str(cp.get('id'))==CID}")
print(f"[app id length] {len(str(cp.get('id')))}")
print(f"[callback_url] {cp.get('callback_url')}")
cbs=cp.get('callback_urls') or []
print(f"[callback_urls count] {len(cbs)}")
for u in cbs: print(f"  - {u}")

# Try direct query of expected app
print(f"\n--- query for 8566085665980242 directly ---")
cp2=requests.get(f"{API}/applications/{EXPECTED}",headers=H,timeout=10)
print(f"HTTP {cp2.status_code}")
print(cp2.text[:600])
