import os, requests
API="https://api.mercadolibre.com"
# Use Angel token (just authorized, can read any item with public scope)
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_ANGEL"]
},timeout=20).json()
T=tok["access_token"]
NEW_RT=tok.get("refresh_token")
print(f"NEW_RT_ANGEL={NEW_RT}")
H={"Authorization":f"Bearer {T}"}
IDS=["5047369636","2806516897","5047380790","2806516505","2806514437","2806512167","5047370382","5047367158","2806503083","2806518457","5047371876","5047368490","2806505831","5047380526","5047380360","5047379494","2804079537","2806516387","2806518883","5047378356"]
sellers={}
titles={}
for sid in IDS:
    r=requests.get(f"{API}/items/MLM{sid}",headers=H,params={"attributes":"id,seller_id,title,status,price,condition,catalog_listing,catalog_product_id"},timeout=20)
    if r.status_code==200:
        d=r.json()
        sellers.setdefault(d.get("seller_id"),[]).append(d["id"])
        titles[d["id"]]=d.get("title","")
        print(f"MLM{sid} seller={d.get('seller_id')} status={d.get('status')} ${d.get('price')} cat={d.get('catalog_listing')} cpid={d.get('catalog_product_id')} title='{(d.get('title') or '')[:65]}'")
    else:
        print(f"MLM{sid} ERR {r.status_code} {r.text[:120]}")
print("\n=== Sellers found ===")
for sid,items in sellers.items():
    print(f"  seller {sid}: {len(items)} items -> {items[:5]}{'...' if len(items)>5 else ''}")
