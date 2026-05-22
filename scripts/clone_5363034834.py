import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

g=requests.get(f"{API}/items/MLM5363034834",headers=H,timeout=10).json()
cpid=g.get("catalog_product_id"); cat=g.get("category_id"); price=g.get("price"); title=g.get("title")
print(f"origen: '{title[:40]}' cpid={cpid} cat={cat} price=${price} status={g.get('status')}")

# Intento 1: catalog_listing True (catálogo puro)
payload={"site_id":"MLM","category_id":cat,"price":price or 349,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","catalog_product_id":cpid,"catalog_listing":True}
print("\n=== Intento catalog_listing=True ===")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    nid=r.json().get("id"); print(f"  NEW: {nid} ✅ status={r.json().get('status')}")
    time.sleep(2)
    g2=requests.get(f"{API}/items/{nid}",headers=H,timeout=10).json()
    print(f"  post: status={g2.get('status')} sub={g2.get('sub_status')}")
    raise SystemExit(0)
else:
    print(f"  body={r.text[:400]}")
