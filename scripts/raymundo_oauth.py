import os,requests,json,base64,sys
from nacl import encoding,public

CODE=sys.argv[1] if len(sys.argv)>1 else "TG-69ea8b0d1eadba0001adeeb2-3338633403"
REDIRECT="https://oauth.pstmn.io/v1/callback"
APP_ID=os.environ["MELI_APP_ID"]
APP_SEC=os.environ["MELI_APP_SECRET"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"
SECRET_NAME="MELI_REFRESH_TOKEN_RAYMUNDO"

print("=== EXCHANGE CODE ===")
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

# Validar /users/me
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"}).json()
print(f"\n=== USUARIO ===\nid: {me.get('id')}\nnickname: {me.get('nickname')}\nname: {me.get('first_name')} {me.get('last_name')}\nemail: {me.get('email')}")

# Guardar RT en archivo ENCRIPTADO con sealed_box de su propio public key de GH (si tiene PAT),
# o escribir en archivo efimero con XOR + fijo, para recuperar localmente
GH_TOK=os.environ.get("GH_PAT","")
if GH_TOK:
    gh_h={"Authorization":f"Bearer {GH_TOK}","Accept":"application/vnd.github+json"}
    kr=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=gh_h).json()
    pk=public.PublicKey(kr["key"].encode(),encoding.Base64Encoder())
    enc=base64.b64encode(public.SealedBox(pk).encrypt(RT.encode())).decode()
    rp=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}",
        headers={**gh_h,"Content-Type":"application/json"},
        json={"encrypted_value":enc,"key_id":kr["key_id"]})
    print(f"\nSECRET saved via GH_PAT: {rp.status_code}")
else:
    # No hay GH_PAT — persistir RT encriptado en el repo con clave del APP_SECRET
    from nacl import secret
    import hashlib
    key=hashlib.sha256(APP_SEC.encode()).digest()
    box=secret.SecretBox(key)
    ct=base64.b64encode(box.encrypt(RT.encode())).decode()
    with open("RT_RAYMUNDO.enc","w") as f: f.write(ct)
    print(f"\nRT guardado encriptado en RT_RAYMUNDO.enc (len={len(ct)})")
