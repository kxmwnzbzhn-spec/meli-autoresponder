import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
TOKENS=[
    ("MELI_REFRESH_TOKEN","JUAN"),
    ("MELI_REFRESH_TOKEN_RAYMUNDO","RAYMUNDO"),
    ("MELI_REFRESH_TOKEN_RAYMUNDO_MAY","RAYMUNDO_MAY"),
    ("MELI_REFRESH_TOKEN_CLARIBEL","CLARIBEL"),
    ("MELI_REFRESH_TOKEN_ASVA","ASVA"),
    ("MELI_REFRESH_TOKEN_DILCIE","DILCIE"),
    ("MELI_REFRESH_TOKEN_MILDRED","MILDRED"),
    ("MELI_REFRESH_TOKEN_BREN","BREN"),
    ("MELI_REFRESH_TOKEN_WILBERT","WILBERT"),
    ("MELI_REFRESH_TOKEN_YC_NEW","YC_NEW"),
    ("MELI_REFRESH_TOKEN_OFICIAL","OFICIAL"),
]
TARGET="AN20251122121541"
print(f"Buscando token que mapee a nick={TARGET}\n")
match_found=False
for env,label in TOKENS:
    RT=os.environ.get(env,"")
    if not RT:
        print(f"  {label:<14} {env:<35} <vacío>"); continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            print(f"  {label:<14} {env:<35} REFRESH FAIL")
            continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        nick=me.get("nickname",""); uid=me.get("id")
        m="  ← MATCH!" if nick==TARGET else ""
        if m: match_found=True
        print(f"  {label:<14} {env:<35} → {nick} ({uid}){m}")
    except Exception as e:
        print(f"  {label:<14} {env:<35} ERR: {e}")

print(f"\n{'MATCH found!' if match_found else 'NO MATCH — need new secret for AN20251122121541'}")
