"""Exchange code → refresh_token y validar."""
import os, requests, json, sys

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
CODE = os.environ["NEW_CODE"]
REDIRECT = "https://oauth.pstmn.io/v1/callback"

print(f"App ID: {APP_ID}")
print(f"Code: {CODE}")
print(f"Intercambiando...")

r = requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"authorization_code","client_id":APP_ID,"client_secret":APP_SECRET,"code":CODE,"redirect_uri":REDIRECT},
    timeout=20)
print(f"HTTP: {r.status_code}")
data = r.json()
print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:600]}")

if "refresh_token" not in data:
    print("\n❌ NO refresh_token recibido. Code probablemente expirado o invalid.")
    sys.exit(1)

REFRESH = data["refresh_token"]
ACCESS = data["access_token"]
print(f"\n✅ refresh_token: {REFRESH}")

H = {"Authorization": f"Bearer {ACCESS}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
print(f"\n=== /users/me ===")
print(f"  ID: {me.get('id')}")
print(f"  Nickname: {me.get('nickname')}")
print(f"  Country: {me.get('country_id')}")
print(f"  Email: {me.get('email','')}")
print(f"  Reputation: {(me.get('seller_reputation') or {}).get('level_id')}")

# Items count
USER_ID = me.get("id")
ic = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?limit=1",headers=H,timeout=10).json()
print(f"  Items totales: {ic.get('paging',{}).get('total',0)}")
