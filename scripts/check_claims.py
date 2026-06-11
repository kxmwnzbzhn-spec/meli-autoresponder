import os, requests, json, time
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; print(f"[ROTATED RT] {tok['refresh_token']}")
H={"Authorization":f"Bearer {AT}"}

me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
UID=me["id"]
print(f"user_id={UID} nick={me.get('nickname')}")
print(f"scopes/permissions check: site={me.get('site_id')} status={me.get('status',{}).get('site_status')}")

endpoints=[
  ("List my claims",f"/post-purchase/v1/claims/search?stage=claim&status=opened&limit=10&player.role=respondent&player.user_id={UID}"),
  ("Claims search v2",f"/v1/claims/search?status=opened&limit=10&player.role=respondent&player.user_id={UID}"),
  ("My orders recent",f"/orders/search?seller={UID}&limit=5&sort=date_desc"),
  ("Claim types",f"/post-purchase/v1/claims/types"),
  ("Mediations",f"/v1/claims/search?status=opened&limit=5&user_id={UID}"),
]
for name,path in endpoints:
  try:
    r=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"\n{name} -> HTTP {r.status_code}")
    print(f"  body[:400]: {r.text[:400]}")
  except Exception as e:
    print(f"{name} -> ERR {e}")
