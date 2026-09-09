import os,json,requests
API="https://api.mercadolibre.com"
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
for app_e,sec_e in [("MELI_APP_ID","MELI_APP_SECRET")]:
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ[app_e],"client_secret":os.environ[sec_e],"refresh_token":rt},timeout=30)
 if r.status_code==200: tok=r.json(); break
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
uid=3658310023
g=requests.get(f"{API}/users/{uid}/applications",headers=H,timeout=20)
print(g.status_code); print(g.text[:2000])
