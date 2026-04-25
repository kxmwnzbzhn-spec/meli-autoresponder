import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

iid = "MLM2890840987"
g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
print(f"=== {iid} (Claribel Go 4 Azul Catálogo) ===")
print(f"  status: {g.get('status')}")
print(f"  available_quantity: {g.get('available_quantity')}")
print(f"  sold_quantity: {g.get('sold_quantity')}")
print(f"  price: ${g.get('price')}")

# Check config
print("\n=== stock_config_claribel.json entry ===")
try:
    with open("stock_config_claribel.json") as f:
        cfg = json.load(f)
    if iid in cfg:
        print(json.dumps(cfg[iid], indent=2, ensure_ascii=False))
    else:
        print(f"❌ {iid} NOT IN CONFIG")
except Exception as e:
    print(f"err: {e}")
