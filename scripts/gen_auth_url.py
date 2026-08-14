import os, requests, urllib.parse
APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]

token=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"client_credentials",
    "client_id":APP_ID,
    "client_secret":APP_SECRET,
},timeout=20)
token.raise_for_status()
access_token=token.json()["access_token"]
app=requests.get(
    f"https://api.mercadolibre.com/applications/{APP_ID}",
    headers={"Authorization":f"Bearer {access_token}"},
    timeout=20,
)
app.raise_for_status()
callback=app.json().get("callback_url")
if not callback:
    raise SystemExit("La app no devolvio callback_url")
url=("https://auth.mercadolibre.com.mx/authorization"
     f"?response_type=code&client_id={APP_ID}"
     f"&redirect_uri={urllib.parse.quote(callback,safe=':/')}")
with open("AUTH_URL.txt","w") as out:
    out.write(url+"\n")
print(f"app={app.json().get('name')} callback={callback}")
print(url)
