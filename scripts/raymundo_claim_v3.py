import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"user_id: {USER_ID}")

CLAIM_ID="2000012579902645"

# Buscar claim en TODOS los stages/statuses
print("\n=== SEARCH CLAIMS ALL ===")
for q in ["?stage=claim","?stage=dispute","?stage=mediations","?status=opened","?status=closed",""]:
    rp=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search{q}",headers=H,timeout=15)
    j=rp.json() if rp.status_code==200 else {}
    items=j.get("data") or []
    print(f"  search{q}: status={rp.status_code} count={len(items)}")
    for c in items[:20]:
        print(f"    id={c.get('id')} stage={c.get('stage')} status={c.get('status')} res={c.get('resource_id')} reason={c.get('reason_id')}")

# Intentar GET individual del claim con scopes diferentes
print(f"\n=== DIRECT GET ===")
for path in [f"/post-purchase/v1/claims/{CLAIM_ID}",
             f"/post-purchase/v2/claims/{CLAIM_ID}",
             f"/v1/claims/{CLAIM_ID}",
             f"/post-purchase/v1/orders/{CLAIM_ID}",
             f"/orders/{CLAIM_ID}"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"  {path}: {rp.status_code}")
    if rp.status_code in (200,401,403):
        print(f"    {rp.text[:500]}")

# Listar ordenes recientes para encontrar match
print(f"\n=== RECENT ORDERS ===")
rp=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&sort=date_desc&limit=20",headers=H,timeout=15)
print(f"  orders: {rp.status_code}")
if rp.status_code==200:
    for o in (rp.json().get("results") or [])[:10]:
        print(f"    order={o.get('id')} status={o.get('status')} pack={o.get('pack_id')} items={[i.get('item',{}).get('id') for i in (o.get('order_items') or [])]}")
