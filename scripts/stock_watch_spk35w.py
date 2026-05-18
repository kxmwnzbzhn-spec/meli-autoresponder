import os, requests, json
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token","client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}

# Search ALL seller items mentioning "secadora"
print("=== All ASVA secadora listings ===")
for sid in [1668713481, 3367276814]:
    r = requests.get("https://api.mercadolibre.com/sites/MLM/search",
        params={"seller_id": sid, "q": "secadora asva"},
        headers=h, timeout=20).json()
    print(f"--- seller {sid}: {r.get('paging',{}).get('total',0)} results ---")
    for item in r.get("results",[])[:15]:
        attrs = {a.get('id'): a.get('value_name') for a in item.get('attributes',[])}
        print(f"  {item.get('id')} | ${item.get('price')} | qty:{item.get('available_quantity'):>3} | sold:{item.get('sold_quantity'):>3} | status:{item.get('status')} | color:{attrs.get('COLOR','-')}")
        print(f"    {item.get('title','')[:90]}")
        print(f"    {item.get('thumbnail')}")
