import os, requests, json
import meli_token
JOBS=[("MLM48766151",538),("MLM23986032",500),("MLM23139920",299),
      ("MLM26894105",1116),("MLM50661134",500),("MLM19588958",650)]
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
print("Cuenta:", me.get("id"), me.get("nickname"), me.get("first_name"), me.get("last_name"))
out=[]
for cp,price in JOBS:
    p=requests.get(f"{API}/products/{cp}",headers=H,timeout=20).json()
    title=p.get("name"); cat=p.get("category_id")
    if not cat:
        dd=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"limit":1,"q":title},headers=H,timeout=15).json()
        if isinstance(dd,list) and dd: cat=dd[0].get("category_id")
    if not cat:
        it=requests.get(f"{API}/products/{cp}/items",headers=H,timeout=15).json().get("results") or []
        if it:
            ci=requests.get(f"{API}/items/{it[0].get('item_id')}?attributes=category_id",headers=H,timeout=12).json()
            cat=ci.get("category_id")
    payload={"site_id":"MLM","title":title,"category_id":cat,"catalog_product_id":cp,
             "catalog_listing":True,"price":price,"currency_id":"MXN","available_quantity":1,
             "buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new"}
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    if r.status_code<300:
        j=r.json(); out.append((cp,j.get("id"),price)); print(f"OK {cp} -> {j.get('id')} ${price} status={j.get('status')} '{(title or '')[:35]}'")
    else:
        print(f"ERR {cp} http={r.status_code} {r.text[:250]}")
print("NEWIDS="+json.dumps(out))
print("DONE")
