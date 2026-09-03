import os, json, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
uid=3654003391
# aplicaciones autorizadas
for path in [f"/users/{uid}/applications",f"/users/{uid}/applications/details",f"/users/me/applications",f"/applications"]:
 g=requests.get(f"{API}{path}",headers=H,timeout=20)
 print(f"\n### {path} → {g.status_code}")
 print(g.text[:1500])
