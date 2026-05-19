import os, requests
SELLERS=[("USER1668","MELI_REFRESH_TOKEN_USER1668",1668713481,"ASVA"),
         ("YC","MELI_REFRESH_TOKEN_YC_NEW",3364413125,"YC"),
         ("WILBERT","MELI_REFRESH_TOKEN_WILBERT",3367276814,"WILBERT")]
for label, var, sid, name in SELLERS:
    rt = os.environ.get(var,"")
    if not rt: continue
    tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}, timeout=20).json()
    if "access_token" not in tok: continue
    h = {"Authorization": f"Bearer {tok['access_token']}"}
    r = requests.get("https://api.mercadolibre.com/items/MLM2940986501", headers=h, timeout=20)
    print(f"--- {name} ({sid}): item HTTP {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"  title: {d.get('title')}")
        print(f"  status: {d.get('status')} | price: {d.get('price')} | qty: {d.get('available_quantity')} | sold: {d.get('sold_quantity')}")
        sh = d.get('shipping') or {}
        print(f"  shipping: {sh.get('logistic_type')} | free: {sh.get('free_shipping')}")
        print(f"  perma: {d.get('permalink')}")
        for i,p in enumerate(d.get("pictures",[])[:3]): print(f"  pic{i}: {p.get('secure_url')}")
        break
