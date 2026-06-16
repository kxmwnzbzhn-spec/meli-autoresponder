import os, requests, time, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
CPID="MLM48919985"
ACCS=[
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("MAYRELY","MELI_REFRESH_TOKEN_MAYRELY"),
  ("YC_NEW","MELI_REFRESH_TOKEN"),
  ("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
]
for nick,sec in ACCS:
  rt=os.environ.get(sec)
  if not rt: print(f"{nick}: no token"); continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
  if r.status_code>=300: print(f"{nick}: oauth fail {r.status_code}"); continue
  AT=r.json()["access_token"]
  H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
  # PATCH probe with empty body
  pp=requests.patch(f"{API}/products/{CPID}",headers=H,json={},timeout=10)
  marker="✅ AUTHORIZED" if pp.status_code in (200,400) else ("❌ FORBIDDEN" if pp.status_code==403 else f"? {pp.status_code}")
  print(f"{nick} (user={me.get('id')} nick={me.get('nickname')}) PATCH -> {pp.status_code} {marker}")
  if pp.status_code in (200,400):
    print(f"  body: {pp.text[:300]}")
