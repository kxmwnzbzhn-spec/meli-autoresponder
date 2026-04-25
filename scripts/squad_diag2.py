import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

iid = "MLM5245310490"
g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
print(f"=== {iid} (Claribel Camuflaje/Squad) ===")
print(f"  status: {g.get('status')}")
print(f"  price: ${g.get('price')}")
print(f"  qty: {g.get('available_quantity')}")
print(f"  free_shipping: {g.get('shipping',{}).get('free_shipping')}")
print(f"  logistic_type: {g.get('shipping',{}).get('logistic_type')}")
print(f"  shipping mode: {g.get('shipping',{}).get('mode')}")
print(f"  seller_id: {g.get('seller_id')}")

# Reputation Claribel
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
rep = me.get("seller_reputation",{})
print(f"\n=== Claribel reputation ===")
print(f"  level_id: {rep.get('level_id')}")
print(f"  power_seller_status: {rep.get('power_seller_status')}")
print(f"  metrics: {json.dumps(rep.get('metrics',{}), indent=2)[:400]}")

# Catalog state
cpid = "MLM37361021"
print(f"\n=== Catálogo {cpid} estado actual ===")
p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H).json()
bbw = p.get("buy_box_winner") or {}
print(f"  buy_box_winner: {bbw}")

print(f"\n=== Competidores ordenados ===")
r2 = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=15", headers=H).json()
for c in r2.get("results",[])[:10]:
    iid_c = c.get("item_id")
    price = c.get("price")
    seller = c.get("seller_id")
    log = c.get("shipping",{}).get("logistic_type") if c.get("shipping") else None
    free = c.get("shipping",{}).get("free_shipping") if c.get("shipping") else None
    is_us = "👈 NOSOTROS" if iid_c == iid else ""
    print(f"  {iid_c} ${price} seller={seller} log={log} free={free} {is_us}")

# Seller of the cheapest external competitor
ext_iids = [c.get("item_id") for c in r2.get("results",[]) if c.get("item_id") != iid][:1]
if ext_iids:
    cei = ext_iids[0]
    cg = requests.get(f"https://api.mercadolibre.com/items/{cei}", headers=H).json()
    print(f"\n=== Competidor más barato {cei} ===")
    print(f"  title: {cg.get('title','')[:60]}")
    print(f"  price: ${cg.get('price')}")
    print(f"  logistic_type: {cg.get('shipping',{}).get('logistic_type')}")
    print(f"  seller: {cg.get('seller_id')}")
    sellid = cg.get('seller_id')
    sg = requests.get(f"https://api.mercadolibre.com/users/{sellid}").json()
    rep2 = sg.get('seller_reputation',{})
    print(f"  competitor reputation level: {rep2.get('level_id')} power: {rep2.get('power_seller_status')}")
