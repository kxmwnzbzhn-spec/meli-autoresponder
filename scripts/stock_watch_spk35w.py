import os, requests, json
# Try Wilbert token
for label, var in [("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),("ASVA","MELI_REFRESH_TOKEN_ASVA"),("USER1668","MELI_REFRESH_TOKEN_USER1668")]:
    rt = os.environ.get(var, "")
    if not rt: continue
    try:
        tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type": "refresh_token","client_id": os.environ["MELI_APP_ID"],
            "client_secret": os.environ["MELI_APP_SECRET"],
            "refresh_token": rt
        }, timeout=20).json()
        if "access_token" not in tok:
            print(f"--- {label}: token refresh failed: {tok.get('message','?')}"); continue
        h = {"Authorization": f"Bearer {tok['access_token']}"}
        r = requests.get("https://api.mercadolibre.com/items/MLM2940664057", headers=h, timeout=20)
        print(f"--- {label}: HTTP {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print("  title:", d.get("title"))
            print("  status:", d.get("status"))
            print("  price:", d.get("price"))
            print("  qty:", d.get("available_quantity"))
            print("  sold:", d.get("sold_quantity"))
            print("  seller:", (d.get("seller") or {}).get("id"))
            print("  perma:", d.get("permalink"))
            sh = d.get("shipping") or {}
            print("  shipping:", sh.get("logistic_type"), "free:", sh.get("free_shipping"))
            for i, p in enumerate(d.get("pictures", [])[:5]):
                print(f"  pic{i}:", p.get("secure_url"))
            break
    except Exception as e:
        print(f"--- {label}: EXC {e}")
