import os,requests
app_id=os.environ["MELI_APP_ID"]
print(f"APP_ID: {app_id}")
# Validar via GET application info
r=requests.get(f"https://api.mercadolibre.com/applications/{app_id}").json()
print(f"App: {r}")
