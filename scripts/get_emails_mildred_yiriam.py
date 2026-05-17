import os,requests,json
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
for nick,env in [("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW")]:
    RT=os.environ.get(env,"")
    print(f"\n=== {nick} ===")
    print(f"  token_len: {len(RT)} prefix: {RT[:10] if RT else 'EMPTY'}")
    if not RT: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT})
    print(f"  oauth http={r.status_code}")
    print(f"  oauth body: {r.text[:400]}")
    try:
        T=r.json().get("access_token")
        if not T: continue
        me_r=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {T}"})
        print(f"  me http={me_r.status_code}")
        print(f"  me body: {me_r.text[:500]}")
    except Exception as e:
        print(f"  ERR: {e}")
