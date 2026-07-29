import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
USER_ID=1668713481

# 1) List current blacklist
for ep in [
    f"/users/{USER_ID}/black_list/users",  # v1
    f"/users/{USER_ID}/black_list",         # v0
    f"/users/{USER_ID}/blacklists",         # alt
    f"/users/{USER_ID}/blocked_users",      # alt
    f"/marketplace/moderation/black_list?seller_id={USER_ID}",
    f"/messaging/moderation/users?seller_id={USER_ID}",
]:
    r=requests.get(f"https://api.mercadolibre.com{ep}",headers=H,timeout=8)
    print(f"\nGET {ep} → {r.status_code}",flush=True)
    print(f"  body: {r.text[:300]}",flush=True)

# 2) Try block a test user (using idiot from the JBL question: 731409256)
TEST_BUYER = 731409256
for ep in [
    (f"/users/{USER_ID}/black_list/users/{TEST_BUYER}", "POST"),
    (f"/users/{USER_ID}/black_list", "POST"),  # body: {"user_id":...}
    (f"/marketplace/moderation/black_list", "POST"),  # body: {"user_id":...}
]:
    url, method = ep
    body = {"user_id": TEST_BUYER}
    r=requests.request(method, f"https://api.mercadolibre.com{url}", headers=H, json=body, timeout=8)
    print(f"\n{method} {url} → {r.status_code}",flush=True)
    print(f"  body: {r.text[:400]}",flush=True)
