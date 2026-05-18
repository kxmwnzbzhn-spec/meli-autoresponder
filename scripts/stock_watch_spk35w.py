import os, requests
rt = os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token","client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": rt
}, timeout=20).json()
if "access_token" not in tok: print("REFRESH FAIL:", tok); raise SystemExit
h = {"Authorization": f"Bearer {tok['access_token']}"}
# who am i
me = requests.get("https://api.mercadolibre.com/users/me", headers=h, timeout=20).json()
print(f"YC seller_id: {me.get('id')} | nickname: {me.get('nickname')} | name: {me.get('first_name','')} {me.get('last_name','')}")
print()
r = requests.get("https://api.mercadolibre.com/items/MLM2940664057", headers=h, timeout=20)
print(f"item HTTP: {r.status_code}")
if r.status_code != 200: print(r.text[:300]); raise SystemExit
d = r.json()
print("title:", d.get("title"))
print("status:", d.get("status"))
print("price:", d.get("price"))
print("qty:", d.get("available_quantity"))
print("sold:", d.get("sold_quantity"))
print("seller_id:", (d.get("seller") or {}).get("id"))
print("perma:", d.get("permalink"))
sh = d.get("shipping") or {}
print("shipping:", sh.get("logistic_type"), "free:", sh.get("free_shipping"))
print("=== pics ===")
for i, p in enumerate(d.get("pictures", [])[:5]):
    print(f"  pic{i}: {p.get('secure_url')}")
