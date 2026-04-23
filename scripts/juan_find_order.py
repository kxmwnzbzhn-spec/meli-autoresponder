import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
OID="2000012579902645"
# GET order directo
o=requests.get(f"https://api.mercadolibre.com/orders/{OID}",headers=H,timeout=15)
print(f"GET /orders/{OID}: {o.status_code}")
print(o.text[:1500])
# Buscar claim por resource_id=OID
s=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?resource_id={OID}",headers=H,timeout=15)
print(f"\nsearch resource_id={OID}: {s.status_code}")
print(s.text[:1500])
# Listar claims abiertos full
a=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&stage=claim&limit=50",headers=H,timeout=15)
print(f"\nopen claims Juan:")
for c in (a.json().get("data") or []):
    print(f"  id={c.get('id')} reason={c.get('reason_id')} res={c.get('resource_id')} stage={c.get('stage')} type={c.get('type')}")

# Tambien buscar con otros parametros
print("\ntodos los estados stage=claim Juan (primeros 20):")
a=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?stage=claim&limit=20&sort=date_desc",headers=H,timeout=15)
for c in (a.json().get("data") or [])[:20]:
    print(f"  id={c.get('id')} status={c.get('status')} reason={c.get('reason_id')} res={c.get('resource_id')}")

# Claribel
r2=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
H2={"Authorization":f"Bearer {r2['access_token']}"}
me2=requests.get("https://api.mercadolibre.com/users/me",headers=H2).json()
print(f"\nClaribel {me2.get('nickname')} {me2.get('id')}")
g=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{OID}",headers=H2,timeout=10)
print(f"  GET claim {OID}: {g.status_code}")
o=requests.get(f"https://api.mercadolibre.com/orders/{OID}",headers=H2,timeout=10)
print(f"  GET order {OID}: {o.status_code}")
a=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened",headers=H2,timeout=10)
print(f"  open claims: {a.status_code} total={a.json().get('paging',{}).get('total',0)}")
for c in (a.json().get("data") or [])[:10]:
    print(f"    id={c.get('id')} reason={c.get('reason_id')} res={c.get('resource_id')}")
