import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]  # Juan

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}

CLAIMS = ["5502933251", "5502636400", "5503096585"]

for cid in CLAIMS:
    print(f"\n{'='*70}")
    print(f"=== Claim {cid} ===")
    g = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}", headers=H, timeout=15).json()
    # Print all fields excluding messages/long arrays
    for k, v in g.items():
        if isinstance(v,(list,dict)) and len(str(v)) > 300:
            print(f"  {k}: {type(v).__name__}({len(v)} entries)")
            if isinstance(v, list) and v:
                print(f"    first: {json.dumps(v[0],ensure_ascii=False)[:300]}")
        else:
            print(f"  {k}: {v}")

# Seller reputation Juan
print(f"\n\n=== Seller reputation Juan ===")
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
rep = me.get("seller_reputation",{})
metrics_claims = rep.get("metrics",{}).get("claims",{})
print(json.dumps(metrics_claims, indent=2))
