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
    
    item_ids = set()
    for st in ["active","paused","closed"]:
        offset = 0
        while True:
            rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}", headers=H).json()
            b = rr.get("results",[])
            if not b: break
            item_ids.update(b); offset += 50
            if offset >= rr.get("paging",{}).get("total",0): break
    
    found = False
    for iid in item_ids:
        g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,status,catalog_listing,available_quantity,catalog_product_id", headers=H).json()
        title = g.get("title","")
        # Look for squad OR charge 6 OR charge6
        tl = title.lower()
        if "squad" in tl or "charge 6" in tl or "charge6" in tl:
            if not found:
                print(f"\n=== {label} ({me.get('nickname')}) ===")
                found = True
            print(f"  {iid} [{g.get('status')}] ${g.get('price')} qty={g.get('available_quantity')} cat_listing={g.get('catalog_listing')} cpid={g.get('catalog_product_id')}")
            print(f"    '{title}'")
