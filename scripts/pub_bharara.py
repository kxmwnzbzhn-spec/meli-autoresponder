import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5511720082"
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
print(f"title: {g.get('title')}")
print(f"price: ${g.get('price')}")
print(f"status: {g.get('status')} sub: {g.get('sub_status')}")
print(f"catalog_listing: {g.get('catalog_listing')}")
print(f"catalog_product_id: {g.get('catalog_product_id')}")
print(f"listing_type_id: {g.get('listing_type_id')}")
print(f"available: {g.get('available_quantity')} sold: {g.get('sold_quantity')}")

CPID=g.get("catalog_product_id")
if CPID:
  i=requests.get(f"{API}/products/{CPID}/items?limit=30",headers=H,timeout=15).json()
  print(f"\n=== competidores CPID {CPID}: {i.get('paging',{}).get('total')} ===")
  for r2 in (i.get("results") or [])[:15]:
    iid=r2.get("item_id"); p=r2.get("price"); lt=r2.get("listing_type_id"); sid=r2.get("seller_id")
    me=" ◄ NUESTRO" if iid==IID else ""
    print(f"  ${p:>8} | {iid} | {lt} | seller={sid}{me}")
  cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
  print(f"\nbuy_box_winner: {cp.get('buy_box_winner')}")
  print(f"CPID name: {cp.get('name','')[:80]}")
