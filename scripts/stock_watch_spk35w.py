import os, requests
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token","client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}
r = requests.get("https://api.mercadolibre.com/items/MLM5356938548", headers=h, timeout=20).json()
print("title:", r.get("title"))
print("status:", r.get("status"))
print("price:", r.get("price"))
print("perma:", r.get("permalink"))
for i, p in enumerate(r.get("pictures",[])[:8]):
    print(f"pic{i}: {p.get('secure_url')}")
