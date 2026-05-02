import os, requests
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
ITEMS = [
    ("MLM2891178657", 1071),
    ("MLM2891178563", 550),
    ("MLM2891178603", 614),
]
for iid, target in ITEMS:
    r = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"price": target}, timeout=15)
    print(f"  {iid} → ${target}: HTTP {r.status_code}")
