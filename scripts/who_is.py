import os, requests
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
TARGET_UID = 3246557656
ACCS = {
    "JUAN":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "DILCIE":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "MILDRED":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "BREN":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "YC_NEW":   os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}
for acc, rt in ACCS.items():
    if not rt: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    at=r.get("access_token")
    if not at: continue
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {at}"}).json()
    print(f"{acc}: uid={me.get('id')} nick={me.get('nickname')}")
