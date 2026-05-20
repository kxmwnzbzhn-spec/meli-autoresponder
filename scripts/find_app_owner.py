import os, requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

# Token via client_credentials (app-level)
tok=requests.post(f"{API}/oauth/token",data={"grant_type":"client_credentials","client_id":CID,"client_secret":CS},timeout=15).json()
T=tok.get("access_token")
print(f"app token ok? {bool(T)}")

# App info
app=requests.get(f"{API}/applications/{CID}",headers={"Authorization":f"Bearer {T}"},timeout=15).json()
print(f"\n=== APP {CID} ===")
print(f"  name: {app.get('name')}")
print(f"  owner_id (user MELI): {app.get('owner_id')}")
print(f"  status: {app.get('status')}")
print(f"  redirect: {app.get('callback_url') or app.get('redirect_uri')}")

owner=app.get("owner_id")
# Mapear owner_id a nombre de cuenta conocido
known={
  3364413125:"YIRIAM/YC_NEW",
  3367276814:"WILBERT",
  3338633403:"RAYMUNDO",
  2681696373:"JUAN",
  1668713481:"ASVA",
}
print(f"\n  → Cuenta dueña: {known.get(owner, 'DESCONOCIDA (no en mi mapa)')}")

# Datos públicos del owner
if owner:
    u=requests.get(f"{API}/users/{owner}",headers={"Authorization":f"Bearer {T}"},timeout=15).json()
    print(f"  nickname: {u.get('nickname')}")
    print(f"  registration: {u.get('registration_date')}")
