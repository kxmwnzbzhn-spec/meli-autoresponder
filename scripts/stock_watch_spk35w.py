import os, requests
for label,var in [("ASVA","MELI_REFRESH_TOKEN_USER1668"),("YC","MELI_REFRESH_TOKEN_YC_NEW"),("WILBERT","MELI_REFRESH_TOKEN_WILBERT")]:
    rt = os.environ.get(var)
    if not rt: continue
    tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}, timeout=20).json()
    if "access_token" not in tok: continue
    h = {"Authorization": f"Bearer {tok['access_token']}"}
    r = requests.get("https://api.mercadolibre.com/items/MLM2911241921", headers=h, timeout=20)
    if r.status_code == 200:
        d = r.json()
        print(f"=== Seller: {label} ===")
        print(f"title:    {d.get('title')}")
        print(f"status:   {d.get('status')} | price: ${d.get('price')} | qty: {d.get('available_quantity')} | sold: {d.get('sold_quantity')}")
        sh = d.get('shipping') or {}
        print(f"shipping: {sh.get('logistic_type')} | free: {sh.get('free_shipping')}")
        print(f"perma:    {d.get('permalink')}")
        print(f"=== pics ===")
        for i,p in enumerate(d.get("pictures",[])[:5]):
            print(f"  pic{i}: {p.get('secure_url')}")
        break
    else:
        print(f"--- {label}: HTTP {r.status_code}")
