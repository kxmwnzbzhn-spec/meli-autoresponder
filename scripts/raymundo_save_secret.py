import os,requests,json,base64,hashlib
from nacl import encoding,public,secret

APP_SEC=os.environ["MELI_APP_SECRET"]
GH_TOK=os.environ["GH_PAT"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"
SECRET_NAME="MELI_REFRESH_TOKEN_RAYMUNDO"

# Leer archivo encriptado
with open("RT_RAYMUNDO.enc") as f: ct=f.read().strip()
key=hashlib.sha256(APP_SEC.encode()).digest()
box=secret.SecretBox(key)
RT=box.decrypt(base64.b64decode(ct)).decode()
print(f"RT desencriptado len={len(RT)}")

# Validar refresh_token sirve
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":APP_SEC,"refresh_token":RT
}).json()
if "access_token" not in r:
    print(f"!!! refresh_token invalido: {r}")
    exit(1)
AT=r["access_token"]
NEW_RT=r.get("refresh_token",RT)
print(f"refresh OK, nuevo RT len={len(NEW_RT)}")

me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"}).json()
print(f"user: {me.get('nickname')} ({me.get('id')})")

# Guardar NEW_RT como secret
gh_h={"Authorization":f"Bearer {GH_TOK}","Accept":"application/vnd.github+json"}
kr=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=gh_h).json()
pk=public.PublicKey(kr["key"].encode(),encoding.Base64Encoder())
enc=base64.b64encode(public.SealedBox(pk).encrypt(NEW_RT.encode())).decode()
rp=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}",
    headers={**gh_h,"Content-Type":"application/json"},
    json={"encrypted_value":enc,"key_id":kr["key_id"]})
print(f"SAVE secret {SECRET_NAME}: {rp.status_code}")

# Eliminar archivo encriptado del repo (ya no se necesita)
import os
os.remove("RT_RAYMUNDO.enc")
print("RT_RAYMUNDO.enc eliminado del disco")
