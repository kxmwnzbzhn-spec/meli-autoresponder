import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}

ITEMS = ["MLM2883448187", "MLM5244765752"]
for iid in ITEMS:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    print(f"\n=== {iid} ===")
    print(f"  Title:     {item.get('title','')[:70]}")
    print(f"  Available: {item.get('available_quantity')}")
    variations = item.get("variations", [])
    if not variations:
        # Item sin variations, intentar con el endpoint /relist
        print(f"  Sin variations, intentando relist...")
        rl = requests.post(f"https://api.mercadolibre.com/items/{iid}/relist", headers=H, json={"available_quantity":1}, timeout=15)
        print(f"  RELIST: HTTP {rl.status_code} {rl.text[:200]}")
        continue
    
    print(f"  VARIATIONS ({len(variations)}):")
    new_vars = []
    for v in variations:
        color = ""
        for ac in v.get("attribute_combinations",[]) or []:
            if "COLOR" in ac.get("id","").upper(): color = ac.get("value_name","")
        new_vars.append({"id": v.get("id"), "available_quantity": 1})
        print(f"    var_id={v.get('id')} color={color} avail={v.get('available_quantity')} → 1")
    
    # PUT con variations array
    rr = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"variations": new_vars}, timeout=20)
    print(f"  RESULT: HTTP {rr.status_code} {rr.text[:200]}")
