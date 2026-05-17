import os,requests,json
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
for nick,env in [("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW")]:
    RT=os.environ.get(env,"")
    if not RT: print(f"{nick}: NO_TOKEN"); continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()
    T=r.get("access_token")
    if not T:
        print(f"{nick}: AUTH_FAIL {r}"); continue
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {T}"}).json()
    print(f"{nick}:")
    print(f"  user_id: {me.get('id')}")
    print(f"  nickname: {me.get('nickname')}")
    print(f"  email: {me.get('email')}")
    print(f"  first_name: {me.get('first_name')}")
    print(f"  last_name: {me.get('last_name')}")
    print(f"  phone: {me.get('phone',{}).get('area_code','')}-{me.get('phone',{}).get('number','')}")
