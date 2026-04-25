import os, requests
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_CLARIBEL","")
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
H = {"Authorization":f"Bearer {r.json()['access_token']}"}
for iid in ["MLM2890840987","MLM5245310484","MLM5245310490","MLM5245310494","MLM5245310498"]:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    print(f"  {iid}: status={g.get('status')} vis={g.get('available_quantity')} '{g.get('title','?')[:50]}'")
