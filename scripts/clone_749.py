import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Get original
g=requests.get(f"https://api.mercadolibre.com/items/MLM2910880749",headers=H).json()
print("Original:",{k:g.get(k) for k in ["id","catalog_product_id","title","category_id","price","listing_type_id","status","sub_status"]})
cpid=g.get("catalog_product_id")
title=g.get("title")
cat=g.get("category_id")
ltype=g.get("listing_type_id") or "gold_pro"

# Build new catalog listing — INCLUDE title + category_id this time
body={
  "title": title,
  "category_id": cat,
  "catalog_listing": True,
  "catalog_product_id": cpid,
  "price": 599,
  "currency_id": "MXN",
  "available_quantity": 1,
  "buying_mode": "buy_it_now",
  "listing_type_id": ltype,
  "condition": "new",
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"90 días"}
  ]
}
print("\n--- Publishing clone ---")
r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
print(f"POST http={r.status_code}")
if r.status_code<300:
    new=r.json()
    print(f"NEW_ID={new.get('id')} price=${new.get('price')} status={new.get('status')}")
    # Also close the under_review one
    print("\n--- Closing old under_review item ---")
    c=requests.put(f"https://api.mercadolibre.com/items/MLM2910880749",headers=H,json={"status":"closed"})
    print(f"CLOSE old http={c.status_code} {c.text[:200]}")
else:
    print(f"ERR: {r.text[:600]}")
