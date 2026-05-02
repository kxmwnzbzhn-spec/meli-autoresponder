import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
sid = me["id"]

# Listar items activos
ids = []
s = 0
while True:
    d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}", headers=H).json()
    got = d.get("results", []) or []
    if not got: break
    ids.extend(got); s += 100
    if s >= d.get("paging",{}).get("total",0): break

print(f"Juan activos: {len(ids)}")
for iid in ids:
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = item.get("title","")
    if any(kw in title.lower() for kw in ["charge","flip","grip"]):
        print(f"\n=== {iid} ===")
        print(f"  Title:     {title[:80]}")
        print(f"  Available: {item.get('available_quantity')}")
        variations = item.get("variations", [])
        if variations:
            print(f"  VARIATIONS ({len(variations)}):")
            for v in variations:
                color = ""
                for ac in v.get("attribute_combinations",[]) or []:
                    if "COLOR" in ac.get("id","").upper(): color = ac.get("value_name","")
                print(f"    var_id={v.get('id')} color={color} avail={v.get('available_quantity')} sold={v.get('sold_quantity',0)}")
        # Buscar match con los IDs del usuario
        if str(iid).endswith("545363") or str(iid).endswith("232593") or "1599970" in str(iid) or "6607419" in str(iid):
            print(f"  ⭐ MATCH con ID del usuario")
