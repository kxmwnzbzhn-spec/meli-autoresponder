import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

p=requests.get(f"{API}/products/MLM69968228",headers=H,timeout=10).json()
print(f"Product MLM69968228: '{p.get('name')}' domain={p.get('domain_id')}")

pi=requests.get(f"{API}/products/MLM69968228/items?limit=10",headers=H,timeout=10).json()
results=pi.get("results") or []
print(f"Competidores ({len(results)}):")
for r in sorted(results,key=lambda x: x.get('price') or 99999):
    print(f"  {r.get('item_id') or r.get('id'):<14} ${r.get('price')} sold={r.get('sold_quantity',0)}")

payload={
    "site_id":"MLM","category_id":"MLM1271","price":798,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","catalog_product_id":"MLM69968228","catalog_listing":True,
}
print(f"\nPublicando a $798")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    new_id=r.json().get("id")
    print(f"  NEW: {new_id} ✅")
    time.sleep(2)
    pw=requests.get(f"{API}/items/{new_id}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: {pw.get('status')} ptw={pw.get('price_to_win')}")
else:
    print(f"  body={r.text[:600]}")
