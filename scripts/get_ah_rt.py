"""Get current rotated refresh token for Adrián."""
import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
new_rt=r.get("refresh_token")
at=r.get("access_token","")[:10]
print("ADRIAN_USER_ID:", r.get("user_id"))
print("ACCESS_TOKEN_PREVIEW:", at+"...")
print("NEW_REFRESH_TOKEN:", new_rt)
print("EXPIRES_IN:", r.get("expires_in"))
