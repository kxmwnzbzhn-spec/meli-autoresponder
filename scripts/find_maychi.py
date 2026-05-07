import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
TOKENS=[
    ("MELI_REFRESH_TOKEN","JUAN"),
    ("MELI_REFRESH_TOKEN_RAYMUNDO","RAYMUNDO"),
    ("MELI_REFRESH_TOKEN_CLARIBEL","CLARIBEL"),
    ("MELI_REFRESH_TOKEN_ASVA","ASVA"),
    ("MELI_REFRESH_TOKEN_DILCIE","DILCIE"),
    ("MELI_REFRESH_TOKEN_MILDRED","MILDRED"),
    ("MELI_REFRESH_TOKEN_BREN","BREN"),
    ("MELI_REFRESH_TOKEN_WILBERT","WILBERT"),
    ("MELI_REFRESH_TOKEN_YC_NEW","YC_NEW"),
    ("MELI_REFRESH_TOKEN_OFICIAL","OFICIAL"),
]
TARGET="RM20260326141639"
print(f"Buscando token que mapee a nick={TARGET}\n")
for env,label in TOKENS:
    RT=os.environ.get(env,"")
    if not RT:
        print(f"  {label:<10} {env:<30} <vacío>"); continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            print(f"  {label:<10} {env:<30} REFRESH FAIL: {r.get('message','?')}")
            continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        nick=me.get("nickname",""); uid=me.get("id")
        match="  ← MATCH!" if nick==TARGET else ""
        print(f"  {label:<10} {env:<30} → {nick} ({uid}){match}")
    except Exception as e:
        print(f"  {label:<10} {env:<30} ERR: {e}")
