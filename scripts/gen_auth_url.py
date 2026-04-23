import os
APP_ID=os.environ["MELI_APP_ID"]
REDIRECT="https://oauth.pstmn.io/v1/callback"
url=f"https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT}"
with open("AUTH_URL.txt","w") as f: f.write(url+"\n")
print(f"escrito AUTH_URL.txt len={len(url)}")
