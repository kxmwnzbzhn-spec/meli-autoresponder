import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
print(f"app_id={os.environ['MELI_APP_ID']}")
print(f"access_token={r.get('access_token')}")
print(f"refresh_token={r.get('refresh_token')}")
print(f"user_id={r.get('user_id')}")
print(f"expires_in={r.get('expires_in')}")
