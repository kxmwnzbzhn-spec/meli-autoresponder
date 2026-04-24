import os,requests,json,base64,unicodedata,re
from nacl import encoding,public

CODES=[
    "TG-69ec021099c03a000100f012-3355056011",
    "TG-69ec0238b1050a00017c59b8-3358792306",
]
REDIRECT="https://oauth.pstmn.io/v1/callback"
APP_ID=os.environ["MELI_APP_ID"]
APP_SEC=os.environ["MELI_APP_SECRET"]
GH=os.environ["GH_PAT"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"

# Public key GitHub para encriptar
gh_h={"Authorization":f"Bearer {GH}","Accept":"application/vnd.github+json"}
kr=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=gh_h).json()
pk=public.PublicKey(kr["key"].encode(),encoding.Base64Encoder())
KEY_ID=kr["key_id"]

def slug(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode('ascii')
    s=re.sub(r'[^A-Za-z0-9]+','_',s).strip('_').upper()
    return s[:30]

users=[]
for code in CODES:
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"authorization_code","client_id":APP_ID,"client_secret":APP_SEC,
        "code":code,"redirect_uri":REDIRECT
    }).json()
    if "refresh_token" not in r:
        print(f"FAIL {code}: {r}")
        continue
    RT=r["refresh_token"]; AT=r["access_token"]
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"}).json()
    info={
        "user_id":me.get("id"),"nickname":me.get("nickname"),
        "first_name":me.get("first_name",""),"last_name":me.get("last_name",""),
        "email":me.get("email",""),"country":me.get("country_id"),
        "reputation":(me.get("seller_reputation") or {}).get("level_id"),
        "rt":RT,
    }
    # Propuesta de nombre: prioridad first_name, luego nickname-basado
    fn=info["first_name"].split()[0] if info["first_name"] else ""
    proposed=fn or info["nickname"][:8]
    info["proposed_name"]=slug(proposed)
    info["secret_name"]=f"MELI_REFRESH_TOKEN_{info['proposed_name']}"
    users.append(info)
    print(f"\n=== {info['nickname']} ({info['user_id']}) ===")
    print(f"  Nombre: {info['first_name']} {info['last_name']}")
    print(f"  Email: {info['email']}")
    print(f"  Reputacion: {info['reputation']}")
    print(f"  Secret propuesto: {info['secret_name']}")
    
    # Guardar refresh_token como GH Secret
    enc=base64.b64encode(public.SealedBox(pk).encrypt(RT.encode())).decode()
    rp=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/{info['secret_name']}",
        headers={**gh_h,"Content-Type":"application/json"},
        json={"encrypted_value":enc,"key_id":KEY_ID})
    print(f"  Secret save: {rp.status_code}")

# Print final summary
print("\n=== USERS ===")
print(json.dumps([{k:v for k,v in u.items() if k!='rt'} for u in users],ensure_ascii=False,indent=2))
