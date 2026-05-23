import os, requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
print(f"APP_ID en secrets: {CID}")
accts={
 "ASVA":"MELI_REFRESH_TOKEN_ASVA","YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW",
 "WILBERT":"MELI_REFRESH_TOKEN_WILBERT","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO",
 "JUAN":"MELI_REFRESH_TOKEN_JUAN","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL",
 "BREN":"MELI_REFRESH_TOKEN_BREN","ANGEL":"MELI_REFRESH_TOKEN_ANGEL",
 "ASGARI":"MELI_REFRESH_TOKEN_ASGARI","RMAYCHI":"MELI_REFRESH_TOKEN_RMAYCHI",
 "AH":"MELI_REFRESH_TOKEN_AH","MC":"MELI_REFRESH_TOKEN_MC",
}
ok=0
for name,env in accts.items():
    rt=os.environ.get(env)
    if not rt: print(f"  {name}: SIN SECRET"); continue
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=20).json()
    at=r.get("access_token")
    if at:
        me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {at}"},timeout=10).json()
        print(f"  {name}: OK nick={me.get('nickname')}")
        ok+=1
    else:
        print(f"  {name}: FALLO {str(r)[:80]}")
print(f"\n{ok}/12 cuentas autenticando con app nueva")
