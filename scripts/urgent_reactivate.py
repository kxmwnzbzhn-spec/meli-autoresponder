import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]

# Get ALL paused items  
ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

# Reactivate every paused with payload {status:active}, ensure qty>=1
for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    qty = g.get("available_quantity",0)
    body = {"status":"active"}
    if qty == 0: body["available_quantity"] = 1
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=15)
    print(f"  ▶️  {iid} qty={qty} → {rp.status_code} {'✅' if rp.status_code==200 else rp.text[:150]}")
print(f"\nTotal reactivados: {len(ids)}")
