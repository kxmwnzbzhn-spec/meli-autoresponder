import os, requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
API="https://api.mercadolibre.com"
# token de la cuenta YC_NEW/Sonix
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json().get("access_token")
me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {T}"},timeout=10).json()
print(f"Cuenta YC_NEW (la del token):")
print(f"  nickname: {me.get('nickname')}")
print(f"  id: {me.get('id')}")
print(f"  email: {me.get('email')}")
print(f"  first_name: {me.get('first_name')} {me.get('last_name')}")
