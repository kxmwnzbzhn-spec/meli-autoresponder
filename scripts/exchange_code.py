import os,requests,json,base64
code="TG-69ea53286e79a00001c45a19-1668713481"
redirect_uri="https://oauth.pstmn.io/v1/callback"
app_id=os.environ["MELI_APP_ID"]
app_secret=os.environ["MELI_APP_SECRET"]

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"authorization_code",
    "client_id":app_id,
    "client_secret":app_secret,
    "code":code,
    "redirect_uri":redirect_uri
},timeout=30).json()

print(f"Response: {json.dumps({k:v for k,v in r.items() if k not in ('access_token','refresh_token')},indent=1)}")

if "access_token" in r:
    tok=r["access_token"]
    rt=r["refresh_token"]
    user_id=r.get("user_id")
    # Info cuenta
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {tok}"},timeout=15).json()
    print(f"\n=== CUENTA AUTORIZADA ===")
    print(f"Nickname: {me.get('nickname')}")
    print(f"ID: {me.get('id')}")
    print(f"Email: {me.get('email')}")
    print(f"Nombre: {me.get('first_name')} {me.get('last_name')}")
    
    # Encode refresh_token en chunks base64 para poder guardarlo
    enc=base64.b64encode(rt.encode()).decode()
    print(f"\n=== REFRESH TOKEN (base64 chunks) ===")
    for i in range(0,len(enc),40):
        print(f"CHUNK:{enc[i:i+40]}")
    print(f"--FIN--")
    print(f"Longitud RT: {len(rt)}")
else:
    print("AUTH FAIL")
