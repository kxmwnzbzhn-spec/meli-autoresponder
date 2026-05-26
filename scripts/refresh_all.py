import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]
ACCS=[("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
      ("JUAN","MELI_REFRESH_TOKEN_JUAN"),("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
      ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),("ASVA","MELI_REFRESH_TOKEN_ASVA"),
      ("BREN","MELI_REFRESH_TOKEN_BREN"),("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
      ("ASGARI","MELI_REFRESH_TOKEN_ASGARI"),("RMAYCHI","MELI_REFRESH_TOKEN_RMAYCHI"),
      ("AH","MELI_REFRESH_TOKEN_AH"),("MC","MELI_REFRESH_TOKEN_MC")]
print("APP_ID:",APP_ID)
print("===SEED_BEGIN===")
for name,env in ACCS:
    rt=(os.environ.get(env) or "").strip()
    if not rt: print(f"{name}: VACIO ({env})"); continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",
        data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":rt},timeout=15)
    j=r.json()
    if r.status_code==200 and "access_token" in j:
        at=j["access_token"]; nrt=j.get("refresh_token") or rt
        try:
            me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {at}"},timeout=12).json()
            uid=me.get("id")
        except: uid="?"
        print(f"{name}: {nrt}  | user_id={uid}")
    else:
        print(f"{name}: ERR http={r.status_code} body={str(j)[:150]}")
print("===SEED_END===")
