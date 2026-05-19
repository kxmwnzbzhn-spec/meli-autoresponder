import os, requests
rt = os.environ["MELI_REFRESH_TOKEN_WILBERT"]
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt
}, timeout=20).json()
if "access_token" not in tok: print("REFRESH FAIL:", tok); raise SystemExit
h = {"Authorization": f"Bearer {tok['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=h, timeout=20).json()
print(f"Wilbert: id={me.get('id')} nick={me.get('nickname')} name={me.get('first_name','')} {me.get('last_name','')}")
r = requests.get("https://api.mercadolibre.com/items/MLM5346655686", headers=h, timeout=20)
print(f"item HTTP: {r.status_code}")
if r.status_code != 200: print(r.text[:300]); raise SystemExit
d = r.json()
print("title:", d.get("title"))
print("status:", d.get("status"))
print("price:", d.get("price"))
print("qty:", d.get("available_quantity"))
print("sold:", d.get("sold_quantity"))
print("perma:", d.get("permalink"))
sh = d.get("shipping") or {}
print("shipping:", sh.get("logistic_type"), "free:", sh.get("free_shipping"))
print("variations:", len(d.get("variations",[])))
for v in d.get("variations",[])[:5]:
    cs = {a.get('id'): a.get('value_name') for a in v.get('attribute_combinations',[])}
    print(f"  var {v.get('id')} price={v.get('price')} qty={v.get('available_quantity')} color={cs.get('COLOR','?')}")
print("=== pics ===")
for i, p in enumerate(d.get("pictures", [])[:5]):
    print(f"  pic{i}: {p.get('secure_url')}")
