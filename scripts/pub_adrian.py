import os, requests, json
import meli_token
JOBS=[("MLM23986032",500),("MLM26894105",1116)]
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
out=[]
for cp,price in JOBS:
    p=requests.get(f"{API}/products/{cp}",headers=H,timeout=20).json()
    title=p.get("name")
    for cat in ["MLM1271","MLM1246"]:
        payload={"site_id":"MLM","title":title,"category_id":cat,"catalog_product_id":cp,
                 "catalog_listing":True,"price":price,"currency_id":"MXN","available_quantity":1,
                 "buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new"}
        r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
        if r.status_code<300:
            j=r.json(); out.append((cp,j.get("id"),price)); print(f"OK {cp} cat={cat} -> {j.get('id')} ${price} '{(title or '')[:35]}'"); break
        else:
            print(f"try {cp} cat={cat} http={r.status_code} {r.text[:150]}")
print("NEWIDS2="+json.dumps(out)); print("DONE")
