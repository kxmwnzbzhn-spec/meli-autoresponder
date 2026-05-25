import os, requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=20).json()
at=r.get("access_token"); nrt=r.get("refresh_token")
uid="?"
if at:
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {at}"},timeout=15).json()
    uid=me.get("id"); nick=me.get("nickname")
print("APP_ID:", CID)
print("USER_ID:", uid, "NICK:", nick if at else "")
print("ACCESS_TOKEN:", at)
print("REFRESH_TOKEN:", nrt)
print("DONE")
