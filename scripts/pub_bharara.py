import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

CPID="MLM37110181"
i=requests.get(f"{API}/products/{CPID}/items?limit=30",headers=H,timeout=15).json()
print(f"raw response keys: {list(i.keys())}")
print(f"paging total: {i.get('paging',{}).get('total')}")
results=i.get("results",[])
print(f"results count: {len(results)}")
for r2 in results[:10]:
  print(f"  raw: {json.dumps({k:r2.get(k) for k in ['item_id','id','price','status','listing_type_id','sold_quantity','seller_id']})}")

# Buy box
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
bb=cp.get("buy_box_winner")
print(f"\nbuy_box_winner full: {bb}")

# Our item
our="MLM3018313225"
g=requests.get(f"{API}/items/{our}",headers=H,timeout=15).json()
print(f"\nNuestro item:")
print(f"  status: {g.get('status')} sub: {g.get('sub_status')}")
print(f"  price: ${g.get('price')}")
print(f"  catalog_listing: {g.get('catalog_listing')}")
print(f"  catalog_product_id: {g.get('catalog_product_id')}")
print(f"  listing_type_id: {g.get('listing_type_id')}")
