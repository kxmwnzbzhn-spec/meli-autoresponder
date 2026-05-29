import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
for sid in ["MLM4299744920","MLM3506962466","MLM2406690589"]:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    print(f"\n{sid}:")
    print(f"  status={g.get('status')} sub={g.get('sub_status')}")
    print(f"  inventory_id={g.get('inventory_id')}")
    print(f"  user_product_id={g.get('user_product_id')}")
    print(f"  available_quantity={g.get('available_quantity')}")
    print(f"  variations_count={len(g.get('variations') or [])}")
    for v in (g.get('variations') or [])[:3]:
        print(f"    var id={v.get('id')} qty={v.get('available_quantity')}")
    print(f"  catalog_product_id={g.get('catalog_product_id')}")
