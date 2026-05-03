import os, requests
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
print(f"Cuenta: {me['nickname']}")
for st in ["active","paused","closed"]:
    rr=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=1",headers=H).json()
    print(f"  {st}: {rr.get('paging',{}).get('total','?')}")
