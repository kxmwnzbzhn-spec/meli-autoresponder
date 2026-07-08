import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
CODE="TG-6a4eb3f4c10676000189e82b-3527910587"
REDIRECT="https://meli-webhook.elite-market-1779161651.workers.dev/oauth/callback"

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
  "grant_type":"authorization_code",
  "client_id":APP_ID,"client_secret":APP_SECRET,
  "code":CODE,"redirect_uri":REDIRECT
},timeout=25).json()

print("=== TOKEN EXCHANGE ===",flush=True)
print(json.dumps(r,indent=2)[:800],flush=True)

if r.get("access_token"):
    print(f"\n✅ SUCCESS",flush=True)
    print(f"USER_ID={r.get('user_id')}",flush=True)
    print(f"REFRESH_TOKEN={r['refresh_token']}",flush=True)
    AT=r["access_token"]
    u=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
    print(f"\nUSER INFO:",flush=True)
    print(f"  nickname: {u.get('nickname')}",flush=True)
    print(f"  id: {u.get('id')}",flush=True)
    print(f"  email: {u.get('email','?')}",flush=True)
    print(f"  site: {u.get('site_id')}",flush=True)
