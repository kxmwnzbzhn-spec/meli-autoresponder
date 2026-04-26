import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

# Items con sus competidores FULL más baratos
ITEMS = [
    ("MLM5245746244", 1116, 150),  # Grip IP68: ext FULL $1116, GAP $150 → $966
    ("MLM5245746252", 1248.96, 150),  # Grip waterproof: ext $1248.96, GAP $150 → $1098.96
    ("MLM5245757608", None, None),  # Grip con luz - ceiling lock $999, sin competencia
]

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

for iid, ext_price, gap in ITEMS:
    print(f"\n=== {iid} ===")
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    cur_price = g.get('price')
    print(f"  current: ${cur_price}")
    
    # Upgrade listing_type to gold_pro (Premium)
    rp1 = requests.post(f"https://api.mercadolibre.com/items/{iid}/listing_type",headers=H,
                       json={"id":"gold_pro"},timeout=15)
    print(f"  Upgrade gold_pro: {rp1.status_code}")
    if rp1.status_code not in (200,201):
        print(f"    {rp1.text[:300]}")
    
    # Lower price aggressively if has FULL competitor
    if ext_price and gap:
        new_price = max(299, ext_price - gap)
        rp2 = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,
                          json={"price": new_price},timeout=15)
        print(f"  Price ${cur_price} → ${new_price}: {rp2.status_code}")
