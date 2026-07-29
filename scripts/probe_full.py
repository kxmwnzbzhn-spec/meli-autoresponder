import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true","x-integrator-id":"20200730"}
USER_ID=1668713481
TB=731409256

# Try various messaging/preventive-block endpoints
for method, ep, body in [
    ("GET", f"/users/{USER_ID}/moderation/black_list", None),
    ("GET", f"/messaging/blocked_users?seller_id={USER_ID}", None),
    ("POST", f"/moderation/black_list", {"seller_id": USER_ID, "user_id": TB}),
    ("POST", f"/users/{USER_ID}/moderation/black_list", {"user_id": TB}),
    ("POST", f"/questions/blacklist", {"item_id": None, "user_id": TB}),
    ("GET", f"/myaccount/mercadolibre/settings/moderation", None),
]:
    r=requests.request(method, f"https://api.mercadolibre.com{ep}", headers=H, json=body if body else None, timeout=8)
    print(f"\n{method} {ep} → {r.status_code}",flush=True)
    print(f"  {r.text[:250]}",flush=True)
