import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

IID = "MLM5245716860"
NEW_PRICE = 1299

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Update price
rp = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={"price": NEW_PRICE}, timeout=15)
print(f"PUT price → {rp.status_code}")
if rp.status_code == 200:
    print(f"  ✅ {IID} ahora a ${rp.json().get('price')}")

# Update stock_config to record base_price
try: cfg = json.load(open("stock_config_claribel.json"))
except: cfg = {}
if IID in cfg:
    cfg[IID]["price"] = NEW_PRICE
    cfg[IID]["base_price"] = NEW_PRICE
    cfg[IID]["ceiling_override"] = NEW_PRICE  # bot no sube arriba
    with open("stock_config_claribel.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
    print(f"  ✅ stock_config: base_price=${NEW_PRICE}, ceiling=${NEW_PRICE}")
