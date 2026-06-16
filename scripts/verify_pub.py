import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}
ITEM="MLM5511675206"
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=12).json()
print(f"item={ITEM}")
print(f"  seller_id: {g.get('seller_id')}")
print(f"  status: {g.get('status')}")
print(f"  sub_status: {g.get('sub_status')}")
print(f"  price: {g.get('price')}")
print(f"  qty: {g.get('available_quantity')}")
print(f"  title: {g.get('title')}")
print(f"  permalink: {g.get('permalink')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  catalog_listing: {g.get('catalog_listing')}")
print(f"  listing_type_id: {g.get('listing_type_id')}")
print(f"  health: {g.get('health')}")
# Check ASVA seller info
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
print(f"\nASVA seller_id={me.get('id')} nickname={me.get('nickname')}")
print(f"match: {g.get('seller_id')==me.get('id')}")
