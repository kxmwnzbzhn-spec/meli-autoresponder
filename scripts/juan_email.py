import os, requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_JUAN"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json().get("access_token")
me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {T}"},timeout=10).json()
print(f"JUAN (dueña de la app):")
print(f"  nickname: {me.get('nickname')}")
print(f"  email: {me.get('email')}")
print(f"  nombre: {me.get('first_name')} {me.get('last_name')}")
print(f"  id: {me.get('id')}")
