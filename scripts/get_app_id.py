import os,requests
# Imprimir primero y ultimo chars para poder armar el URL
app_id=os.environ["MELI_APP_ID"]
# MELI masks, pero podemos exportar en base64 a un archivo
import base64
enc=base64.b64encode(app_id.encode()).decode()
# chunk en partes
for i in range(0,len(enc),20):
    print(f"CHUNK_{i}:{enc[i:i+20]}")
# tambien intentar con un GET auth endpoint y parsear de vuelta
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":app_id,"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
tok=r.get("access_token","")
# El access_token contiene info - parsearlo
print(f"user_id: {r.get('user_id','')}")
# Try /users/me to validate
if tok:
    r2=requests.get(f"https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {tok}"}).json()
    # Ver integrations/apps conectadas
    r3=requests.get(f"https://api.mercadolibre.com/users/me/applications",headers={"Authorization":f"Bearer {tok}"})
    print(f"applications: {r3.status_code} {r3.text[:500]}")
