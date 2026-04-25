import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_ASVA","")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
USER_ID = me["id"]

# Search all active speakers
print("=== ACTIVE BOCINAS ===")
for st in ["active"]:
    offset = 0
    while True:
        r = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}", headers=H).json()
        batch = r.get("results", [])
        if not batch: break
        for iid in batch:
            g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
            t = g.get("title","")
            cat = g.get("category_id","")
            if "MLM59800" in cat or "bocina" in t.lower() or "speaker" in t.lower():
                print(f"  {iid} ${g.get('price')} qty={g.get('available_quantity')} free={g.get('shipping',{}).get('free_shipping')} cat={cat}")
                print(f"    title: '{t}'")
                # show variations if any
                for v in g.get("variations",[]):
                    for ac in v.get("attribute_combinations",[]):
                        if ac.get("id")=="MODEL":
                            print(f"    var MODEL: {ac.get('value_name')}")
        offset += 50
        if offset >= r.get("paging",{}).get("total",0): break
