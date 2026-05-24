import os, requests
import meli_token
ACCTS=["ASVA","YC_NEW","WILBERT","RAYMUNDO","JUAN","CLARIBEL","BREN","ANGEL","ASGARI","RMAYCHI","AH","MC"]
for a in ACCTS:
    env=f"MELI_REFRESH_TOKEN_{a}"
    rt=os.environ.get(env)
    if not rt: print(f"{a}: (sin secret)"); continue
    try:
        at=meli_token.refresh(rt).json().get("access_token")
        me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {at}"},timeout=20).json()
        print(f"{a}: id={me.get('id')} nick={me.get('nickname')} nombre={me.get('first_name','')} {me.get('last_name','')}".strip())
    except Exception as e:
        print(f"{a}: ERR {type(e).__name__}")
print("DONE")
