"""Fetch full chart from /catalog/charts/5915675."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
rr=requests.get(f"{API}/catalog/charts/5915675",headers=H,timeout=10)
print(f"HTTP {rr.status_code}")
print(json.dumps(rr.json(), indent=2, ensure_ascii=False))
