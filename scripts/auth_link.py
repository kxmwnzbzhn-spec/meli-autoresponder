"""Construct the MELI MX authorization URL for re-authorizing Adrián."""
import os, requests
APP_ID=os.environ["MELI_APP_ID"]
# Try to discover registered redirect_uris from MELI App API
# Otherwise use common candidates the user has used before
candidates=[
    "https://kxmwnzbzhn-spec.github.io/meli-callback",
    "https://meli.luisvargas.dev/callback",
    "https://api.mercadolibre.com/oauth/callback",
]
print(f"APP_ID={APP_ID}")
print(f"\n=== Authorization URLs (try in this order) ===\n")
for u in candidates:
    url=f"https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id={APP_ID}&redirect_uri={u}"
    print(f"URL ({u}):")
    print(f"  {url}")
    print()

# Also probe MELI App info if app has registered redirect_uri
# This requires app-level credentials which we have
try:
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
      "grant_type":"client_credentials",
      "client_id":APP_ID,
      "client_secret":os.environ["MELI_APP_SECRET"]},timeout=15).json()
    app_token=r.get("access_token")
    if app_token:
        ai=requests.get(f"https://api.mercadolibre.com/applications/{APP_ID}",
            headers={"Authorization":f"Bearer {app_token}"},timeout=10).json()
        print(f"=== App info ===")
        print(f"  name: {ai.get('name')}")
        print(f"  callback_url: {ai.get('callback_url')}")
        if ai.get("callback_url"):
            real=ai["callback_url"]
            real_url=f"https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id={APP_ID}&redirect_uri={real}"
            print(f"\n=== ACTUAL AUTHORIZATION URL ===\n{real_url}")
except Exception as e:
    print(f"  app info err: {e}")
