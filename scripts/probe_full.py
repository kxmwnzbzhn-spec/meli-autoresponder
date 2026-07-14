import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
USER_ID=1668713481

IID="MLM5656253306"

# 1) Item details + fulfillment info
print(f"\n=== 1. ITEM {IID} ===",flush=True)
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=10).json()
print(f"  title: {g.get('title','?')[:70]}",flush=True)
print(f"  status: {g.get('status')} sub={g.get('sub_status')}",flush=True)
print(f"  price: ${g.get('price')} qty: {g.get('available_quantity')}",flush=True)
print(f"  catalog_product_id: {g.get('catalog_product_id')}",flush=True)
sh=g.get("shipping",{})
print(f"  shipping mode: {sh.get('mode')} logistic_type: {sh.get('logistic_type')}",flush=True)
print(f"  inventory_id: {g.get('inventory_id')}",flush=True)
user_product_id=g.get("user_product_id")
print(f"  user_product_id: {user_product_id}",flush=True)

# 2) Check user fulfillment onboarding
print(f"\n=== 2. USER FULFILLMENT STATUS ===",flush=True)
u=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}",headers=H,timeout=10).json()
print(f"  status.mercadopago_account_type: {u.get('status',{}).get('mercadopago_account_type')}",flush=True)
tag=u.get("tags",[])
print(f"  tags: {tag[:10]}",flush=True)

# 3) Try fulfillment endpoints
for ep in [
    "/fulfillment/inventory/warehouses",
    f"/users/{USER_ID}/fulfillment/inventory/eligibility",
    f"/fulfillment/inventory/eligibility?item_ids={IID}",
    f"/inventories/{IID}",
    f"/users/{USER_ID}/products/search?limit=5",
    "/fbm/inbound_shipments",  # experimental
]:
    r=requests.get(f"https://api.mercadolibre.com{ep}",headers=H,timeout=10)
    ct=r.headers.get('content-type','')
    body=r.text[:300] if 'json' in ct or r.status_code!=404 else "..."
    print(f"\n  GET {ep} → {r.status_code}",flush=True)
    print(f"    body: {body[:400]}",flush=True)
