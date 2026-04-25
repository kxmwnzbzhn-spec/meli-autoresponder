import os, requests
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN","MELI_REFRESH_TOKEN"),("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),("MILDRED","MELI_REFRESH_TOKEN_MILDRED")
]
for label, env in ACCOUNTS:
    RT = os.environ.get(env,"")
    if not RT: continue
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
    USER_ID = me.get("id")
    print(f"\n=== {label} ({me.get('nickname')}) ===")
    
    item_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}", headers=H).json()
        b = rr.get("results",[])
        if not b: break
        item_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    for iid in item_ids:
        g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,available_quantity", headers=H).json()
        title = g.get("title","")
        if "squad" in title.lower():
            print(f"  {iid}: '{title}' ${g.get('price')} qty={g.get('available_quantity')} cat_listing={g.get('catalog_listing')} cpid={g.get('catalog_product_id')}")
