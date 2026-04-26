import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}

# 1) Try with status=all, all stages, all types
print("=== Variantes de query Juan ===\n")
queries = [
    "/post-purchase/v1/claims/search?limit=20",
    "/post-purchase/v1/claims/search?limit=20&status=opened",
    "/post-purchase/v1/claims/search?limit=20&status=closed",
    "/post-purchase/v1/claims/search?limit=20&type=mediations",
    "/post-purchase/v1/claims/search?limit=20&type=returns",
    "/post-purchase/v1/claims/search?limit=20&date_created.from=2026-04-25T00:00:00.000Z&date_created.to=2026-04-26T06:00:00.000Z",
    "/post-purchase/v1/claims/search?limit=20&sort=date_created_desc",
    "/v1/claims/search?limit=20",
]
for q in queries:
    rr = requests.get(f"https://api.mercadolibre.com{q}",headers=H,timeout=15)
    if rr.status_code != 200:
        print(f"  ❌ {q[:80]} → {rr.status_code}: {rr.text[:120]}")
        continue
    data = rr.json()
    items = data.get("data") or data.get("results") or []
    print(f"  ✅ {q[:80]} → {len(items)} items")
    for c in items[:5]:
        cid = c.get("id"); cd = c.get("date_created",""); st = c.get("status",""); t = c.get("type","")
        print(f"     {cid} | {st} | {t} | {cd}")
    print()

# Also check resource: orders with claim
print("\n=== Orders ayer que tienen claims ===")
ord_resp = requests.get("https://api.mercadolibre.com/orders/search?seller=2681696373&order.date_created.from=2026-04-25T06:00:00.000Z&order.date_created.to=2026-04-26T06:00:00.000Z&limit=50",headers=H,timeout=20).json()
for o in (ord_resp.get("results") or [])[:30]:
    if o.get("mediations"):
        print(f"  Order {o.get('id')} | mediations: {o.get('mediations')}")

# 3) MELI account claims
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"\n=== Reputation Juan: nivel {me.get('seller_reputation',{}).get('level_id')} ===")
metrics = me.get("seller_reputation",{}).get("metrics",{})
print(f"Claims metrics: {json.dumps(metrics.get('claims',{}),indent=2)[:600]}")
