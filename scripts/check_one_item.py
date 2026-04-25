import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")

# Try with all account tokens to find owner
for acct, env_var in [("Juan","MELI_REFRESH_TOKEN"),("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),
                      ("ASVA","MELI_REFRESH_TOKEN_ASVA"),("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO")]:
    RT = os.getenv(env_var,"")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        g = requests.get("https://api.mercadolibre.com/items/MLM5241635216", headers=H).json()
        if g.get("seller_id"):
            print(f"=== {acct} ===")
            print(f"  status: {g.get('status')}")
            print(f"  title: {g.get('title')}")
            print(f"  cond: {g.get('condition')}")
            print(f"  price: ${g.get('price')}")
            print(f"  available_quantity: {g.get('available_quantity')}")
            print(f"  sold_quantity: {g.get('sold_quantity')}")
            print(f"  seller_id: {g.get('seller_id')}")
            print(f"  cat: {g.get('category_id')}")
            print(f"  catalog_pid: {g.get('catalog_product_id')}")
            print(f"  variations: {len(g.get('variations',[]) or [])}")
            for v in (g.get('variations') or []):
                color = "?"
                for ac in v.get("attribute_combinations",[]):
                    if ac.get("id")=="COLOR": color = ac.get("value_name","?")
                print(f"    [{color}] visible={v.get('available_quantity')} sold={v.get('sold_quantity')}")
            break
    except Exception as e:
        print(f"  {acct}: err {e}")
