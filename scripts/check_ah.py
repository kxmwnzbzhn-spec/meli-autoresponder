import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
print(f"seller={me.get('id')} nick={me.get('nickname')}")
print(f"status: shipping={me.get('shipping_modes')} permalink={me.get('permalink')}")
print(f"site={me.get('site_id')} country={me.get('country_id')}")
print(f"seller_reputation={me.get('seller_reputation',{})}")
print(f"status_list={me.get('status')}")

UID=me["id"]
# Adrián's items + their categories
for st in ("active","paused","under_review"):
    r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=20",headers=H,timeout=15).json()
    ids=r.get("results") or []
    if ids:
        print(f"\n=== {st} ({len(ids)}) ===")
        mg=requests.get(f"{API}/items",headers=H,params={"ids":",".join(ids[:20]),"attributes":"id,title,category_id,catalog_product_id,price,status,sub_status"},timeout=20).json()
        for x in mg:
            if x.get("code")==200:
                b=x["body"]
                print(f"  {b['id']} cat={b.get('category_id')} cpid={b.get('catalog_product_id')} ${b.get('price')} {b.get('status')} | {(b.get('title') or '')[:60]}")

# Try category lookup
print("\n=== category MLM179232 lookup ===")
r=requests.get(f"{API}/categories/MLM179232",headers=H,timeout=10)
print(f"  HTTP {r.status_code} {r.text[:200]}")
print("\n=== category MLM177562 lookup (my fallback) ===")
r=requests.get(f"{API}/categories/MLM177562",headers=H,timeout=10)
print(f"  HTTP {r.status_code} {r.text[:200]}")

# Try valid perfume category — MLM35935 is Belleza Y Cuidado Personal
print("\n=== /sites/MLM/categories root ===")
r=requests.get(f"{API}/sites/MLM/categories",headers=H,timeout=10).json()
for c in r[:30]:
    if "perfum" in (c.get("name") or "").lower() or "belleza" in (c.get("name") or "").lower():
        print(f"  {c.get('id')} {c.get('name')}")
