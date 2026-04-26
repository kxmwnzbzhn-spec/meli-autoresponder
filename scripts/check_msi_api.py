import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
USER_ID = me["id"]

# Check account-level installments / promotions endpoints
endpoints = [
    f"/users/{USER_ID}/installments",
    f"/users/{USER_ID}/promotions",
    f"/users/{USER_ID}/coupons",
    f"/sellers/{USER_ID}/installments",
    f"/seller-services/{USER_ID}/installments",
    f"/sites/MLM/installments",
    f"/users/{USER_ID}/promotions/seller_promotions",
    f"/users/{USER_ID}/seller-promotions",
]

print("=== Endpoints MSI/Cuotas (GET) ===")
for ep in endpoints:
    rr = requests.get(f"https://api.mercadolibre.com{ep}", headers=H, timeout=10)
    print(f"  {ep} → {rr.status_code}")
    if rr.status_code in (200,201):
        print(f"    {rr.text[:400]}")

# Check item current installments (read-only field)
iid = "MLM5245746244"
g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
print(f"\n=== Item {iid} ===")
print(f"  installments: {json.dumps(g.get('installments'), indent=2)}")
print(f"  accepts_mercadopago: {g.get('accepts_mercadopago')}")

# Try setting installments via PUT (probably won't work)
print(f"\n=== Test PUT installments (debería fallar) ===")
rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, 
                  json={"installments": {"quantity": 12, "rate": 0}}, timeout=15)
print(f"  PUT → {rp.status_code}: {rp.text[:300]}")

# Check seller status for installments
rep = me.get("seller_reputation",{})
print(f"\n=== Cuenta Claribel ===")
print(f"  reputation: {rep.get('level_id')} | power_seller: {rep.get('power_seller_status')}")
print(f"  selling_capacity: {me.get('selling_capacity','?')}")
