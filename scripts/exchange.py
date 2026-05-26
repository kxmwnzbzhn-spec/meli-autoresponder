import os, requests, sys, json
code=os.environ["CODE"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"authorization_code",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "code":code,
    "redirect_uri":"https://meli-webhook.elite-market-1779161651.workers.dev/oauth/callback"
},timeout=20)
print("HTTP",r.status_code)
print(r.text)
if r.status_code==200:
    d=r.json()
    # Get user info
    u=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {d['access_token']}"},timeout=20).json()
    print(f"\n=== USER ===\nuser_id={u.get('id')}\nnickname={u.get('nickname')}\nemail={u.get('email')}")
    print(f"\n=== REFRESH_TOKEN ===\n{d.get('refresh_token')}\n=== END ===")
