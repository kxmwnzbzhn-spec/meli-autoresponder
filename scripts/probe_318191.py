import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM2967318191"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
print(f"\n=== {sid} ===")
print(f"status={g.get('status')} sub_status={g.get('sub_status')}")
print(f"price=${g.get('price')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")
print(f"inventory_id={g.get('inventory_id')} (Full/FBM?)")
print(f"user_product_id={g.get('user_product_id')}")
print(f"catalog_product_id={g.get('catalog_product_id')} catalog_listing={g.get('catalog_listing')}")
print(f"title='{g.get('title')}'")

# Try to reactivate
print(f"\nTrying to reactivate now...")
if g.get('status')=='paused':
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=15)
    print(f"PUT active+qty=1: {r.status_code} {r.text[:300] if r.status_code>=400 else 'OK'}")
    g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    print(f"AFTER: status={g2.get('status')} qty={g2.get('available_quantity')}")
else:
    print(f"  ya está {g.get('status')} — no action needed")
