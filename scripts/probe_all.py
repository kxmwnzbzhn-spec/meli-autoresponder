import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
IID="MLM2911241921"

accounts={
  "AH": "MELI_REFRESH_TOKEN_AH",
  "ASVA": "MELI_REFRESH_TOKEN_ASVA",
  "JUAN": "MELI_REFRESH_TOKEN_JUAN",
  "RAYMUNDO": "MELI_REFRESH_TOKEN_RAYMUNDO",
  "WILBERT": "MELI_REFRESH_TOKEN_WILBERT",
  "CLARIBEL": "MELI_REFRESH_TOKEN_CLARIBEL",
  "DILCIE": "MELI_REFRESH_TOKEN_DILCIE",
  "BREN": "MELI_REFRESH_TOKEN_BREN",
  "MILDRED": "MELI_REFRESH_TOKEN_MILDRED",
  "YC_NEW": "MELI_REFRESH_TOKEN_YC_NEW",
  "MG20260424": "MELI_REFRESH_TOKEN_MG20260424",
}
for acct,key in accounts.items():
  rt=os.environ.get(key)
  if not rt:
    print(f"{acct}: no token in env")
    continue
  try:
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20)
    if r.status_code>=400:
      print(f"{acct}: token refresh failed {r.status_code}")
      continue
    AT=r.json()["access_token"]
    H={"Authorization":f"Bearer {AT}"}
    g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,seller_id,catalog_product_id",headers=H,timeout=15)
    print(f"{acct}: {g.status_code}", g.text[:300] if g.status_code<400 else "")
  except Exception as e:
    print(f"{acct}: exception {e}")
