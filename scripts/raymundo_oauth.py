import os,requests,json,base64
from nacl import encoding,public

CODE="TG-69ea8b0d1eadba0001adeeb2-3338633403"
REDIRECT="https://oauth.pstmn.io/v1/callback"
APP_ID=os.environ["MELI_APP_ID"]
APP_SEC=os.environ["MELI_APP_SECRET"]
GH_TOK=os.environ["GH_PAT"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"
SECRET_NAME="MELI_REFRESH_TOKEN_RAYMUNDO"

# 1) Intercambiar code -> refresh_token
print("=== EXCHANGE CODE ===")
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"authorization_code","client_id":APP_ID,"client_secret":APP_SEC,
    "code":CODE,"redirect_uri":REDIRECT
}).json()
print(json.dumps({k:v for k,v in r.items() if k!="refresh_token"},indent=2))
if "refresh_token" not in r:
    print("!!! FALLO")
    exit(1)
RT=r["refresh_token"]
AT=r["access_token"]
print(f"RT obtenido len={len(RT)}")

# 2) Validar /users/me
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"}).json()
print(f"\n=== USUARIO ===")
for k in ("id","nickname","first_name","last_name","email","country_id","site_id","user_type","status","seller_reputation"):
    v=me.get(k)
    if k=="seller_reputation" and v:
        print(f"  reputation: level={v.get('level_id')} power_seller={v.get('power_seller_status')}")
    else:
        print(f"  {k}: {v}")

# 3) Guardar como GitHub Secret (libsodium sealed_box)
print(f"\n=== GUARDAR SECRET {SECRET_NAME} ===")
gh_h={"Authorization":f"Bearer {GH_TOK}","Accept":"application/vnd.github+json"}
# obtener public key
kr=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=gh_h).json()
pk_b64=kr["key"]; kid=kr["key_id"]
pk=public.PublicKey(pk_b64.encode(),encoding.Base64Encoder())
sealed=public.SealedBox(pk).encrypt(RT.encode())
enc=base64.b64encode(sealed).decode()
# PUT secret
rp=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}",
    headers={**gh_h,"Content-Type":"application/json"},
    json={"encrypted_value":enc,"key_id":kid})
print(f"  secret saved: {rp.status_code}")
