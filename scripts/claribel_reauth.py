import os,requests,json,base64,sys,hashlib
from nacl import encoding,public,secret

CODE="TG-69eb7baccb348f00014b2d91-3348766821"
REDIRECT="https://oauth.pstmn.io/v1/callback"
APP_ID=os.environ["MELI_APP_ID"]
APP_SEC=os.environ["MELI_APP_SECRET"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"
SECRET_NAME="MELI_REFRESH_TOKEN_CLARIBEL"

# Intercambiar
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"authorization_code","client_id":APP_ID,"client_secret":APP_SEC,
    "code":CODE,"redirect_uri":REDIRECT
}).json()
print(json.dumps({k:v for k,v in r.items() if k!="refresh_token"},indent=2))
if "refresh_token" not in r:
    print("!!! FALLO")
    sys.exit(1)
RT=r["refresh_token"]
AT=r["access_token"]
# Validar
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"}).json()
print(f"\nUSUARIO: {me.get('nickname')} ({me.get('id')})")
print(f"name: {me.get('first_name')} {me.get('last_name')}")

# Guardar en GitHub Secret
GH=os.environ.get("GH_PAT","")
if GH:
    gh_h={"Authorization":f"Bearer {GH}","Accept":"application/vnd.github+json"}
    kr=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=gh_h).json()
    pk=public.PublicKey(kr["key"].encode(),encoding.Base64Encoder())
    enc=base64.b64encode(public.SealedBox(pk).encrypt(RT.encode())).decode()
    rp=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}",
        headers={**gh_h,"Content-Type":"application/json"},
        json={"encrypted_value":enc,"key_id":kr["key_id"]})
    print(f"\nSECRET {SECRET_NAME}: {rp.status_code}")
else:
    # fallback: encriptar con APP_SECRET y guardar en repo
    key=hashlib.sha256(APP_SEC.encode()).digest()
    box=secret.SecretBox(key)
    ct=base64.b64encode(box.encrypt(RT.encode())).decode()
    with open("RT_CLARIBEL.enc","w") as f: f.write(ct)
    print(f"\nRT_CLARIBEL.enc guardado (fallback)")
