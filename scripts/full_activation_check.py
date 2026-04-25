import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"=== Claribel ({me.get('nickname')}) {USER_ID} ===")

rep = me.get("seller_reputation",{})
print(f"\nReputación:")
print(f"  level_id: {rep.get('level_id')}")
print(f"  power_seller_status: {rep.get('power_seller_status')}")
print(f"  sales 365d: {rep.get('metrics',{}).get('sales',{}).get('completed','?')}")
print(f"  Reputación inicio (last_year): {me.get('seller_experience','?')}")

# Endpoints to query FULL eligibility
endpoints = [
    f"/users/{USER_ID}/inventory_health",
    f"/users/{USER_ID}/fulfillment_status",
    f"/users/{USER_ID}/fulfillment",
    f"/users/{USER_ID}/seller/inventory_health",
    f"/inventories/seller/{USER_ID}",
    f"/inventories/{USER_ID}",
    f"/users/{USER_ID}/full_eligibility",
    f"/sites/MLM/users/{USER_ID}/fulfillment_eligibility",
    f"/users/{USER_ID}/seller-services/full",
    f"/sites/MLM/categories/MLM59800/shipping_options",
]

print("\n=== Probando endpoints FULL ===")
for ep in endpoints:
    r = requests.get(f"https://api.mercadolibre.com{ep}", headers=H, timeout=10)
    code = r.status_code
    if code in (200, 201):
        print(f"  ✅ {ep} → {code}")
        try:
            data = r.json()
            print(f"     {json.dumps(data, ensure_ascii=False)[:600]}")
        except: print(f"     {r.text[:300]}")
    elif code == 404:
        print(f"  ❌ {ep} → 404")
    else:
        print(f"  ⚠️ {ep} → {code}: {r.text[:150]}")

# Try to request FULL (POST endpoints)
print("\n=== POST FULL request endpoints ===")
post_endpoints = [
    f"/users/{USER_ID}/fulfillment/request",
    f"/users/{USER_ID}/fulfillment_activation",
    f"/seller-services/{USER_ID}/full/activate",
    f"/inventories/seller/{USER_ID}/activate",
]
for ep in post_endpoints:
    r = requests.post(f"https://api.mercadolibre.com{ep}", headers=H, json={}, timeout=10)
    print(f"  {ep} → {r.status_code}: {r.text[:200]}")

# Inventory status (sometimes this works)
print("\n=== Inventory status endpoints ===")
r = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&logistic_type=fulfillment&limit=1", headers=H, timeout=10).json()
print(f"Items con logistic_type=fulfillment: {r.get('paging',{}).get('total','?')}")

# Eligibility — sometimes via tags
print("\n=== User tags & status ===")
print(f"  tags: {me.get('tags',[])}")
print(f"  status: {json.dumps(me.get('status',{}), indent=2)[:500]}")
