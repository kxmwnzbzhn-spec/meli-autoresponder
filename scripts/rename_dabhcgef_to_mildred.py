import os,requests,json,base64
from nacl import encoding,public

APP_ID=os.environ["MELI_APP_ID"]
APP_SEC=os.environ["MELI_APP_SECRET"]
RT_OLD=os.environ["MELI_REFRESH_TOKEN_DABHCGEF"]
GH=os.environ["GH_PAT"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"

# Refresh para obtener nuevo refresh_token (MELI rota)
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":RT_OLD
}).json()
if "refresh_token" not in r:
    print(f"FAIL refresh: {r}")
    exit(1)
RT_NEW=r["refresh_token"]
AT=r["access_token"]
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"}).json()
print(f"User: {me.get('nickname')} ({me.get('id')})")
print(f"Email: {me.get('email')}")

# Guardar como MELI_REFRESH_TOKEN_MILDRED
gh_h={"Authorization":f"Bearer {GH}","Accept":"application/vnd.github+json"}
kr=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=gh_h).json()
pk=public.PublicKey(kr["key"].encode(),encoding.Base64Encoder())
enc=base64.b64encode(public.SealedBox(pk).encrypt(RT_NEW.encode())).decode()
rp=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/MELI_REFRESH_TOKEN_MILDRED",
    headers={**gh_h,"Content-Type":"application/json"},
    json={"encrypted_value":enc,"key_id":kr["key_id"]})
print(f"SAVE MELI_REFRESH_TOKEN_MILDRED: {rp.status_code}")

# Borrar MELI_REFRESH_TOKEN_DABHCGEF
rd=requests.delete(f"https://api.github.com/repos/{REPO}/actions/secrets/MELI_REFRESH_TOKEN_DABHCGEF",headers=gh_h)
print(f"DELETE MELI_REFRESH_TOKEN_DABHCGEF: {rd.status_code}")
