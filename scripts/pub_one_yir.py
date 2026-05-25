import os, requests
import meli_token
CPID="MLM43902928"; PRICE=499; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=20).json()
title=p.get("name"); 
# categoria desde un competidor
cat=None
it=requests.get(f"{API}/products/{CPID}/items",headers=H,timeout=20).json().get("results") or []
if it:
    ci=requests.get(f"{API}/items/{it[0].get('item_id')}?attributes=category_id",headers=H,timeout=15).json()
    cat=ci.get("category_id")
print(f"catalogo: '{title}' cat={cat} ofertas={len(it)}")
payload={"site_id":"MLM","title":title,"category_id":cat,"catalog_product_id":CPID,
         "catalog_listing":True,"price":PRICE,"currency_id":"MXN","available_quantity":1,
         "buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new"}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"publish http={r.status_code}")
if r.status_code<300:
    j=r.json(); print(f"NEW={j.get('id')} status={j.get('status')} price={j.get('price')} {j.get('permalink')}")
else:
    print(f"body={r.text[:400]}")
print("DONE")
