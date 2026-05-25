import os, requests, json
import meli_token
JOBS=[("MLM5363034842",449),("MLM2916942827",449),("MLM5364336602",799)]
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
for iid,price in JOBS:
    s=requests.get(f"{API}/items/{iid}",headers=H,timeout=20).json()
    cpid=s.get("catalog_product_id"); lt=s.get("listing_type_id") or "gold_pro"
    print(f"\n=== {iid} '{s.get('title','')[:45]}' cpid={cpid} lt={lt} status={s.get('status')} ===")
    if cpid:
        payload={"site_id":"MLM","catalog_product_id":cpid,"catalog_listing":True,
                 "price":price,"currency_id":"MXN","available_quantity":1,
                 "buying_mode":"buy_it_now","listing_type_id":lt,"condition":"new"}
    else:
        pics=[{"id":p["id"]} for p in (s.get("pictures") or []) if p.get("id")]
        attrs=[{"id":a["id"],"value_id":a.get("value_id"),"value_name":a.get("value_name")} for a in (s.get("attributes") or []) if a.get("id")]
        payload={"site_id":"MLM","title":s.get("title"),"category_id":s.get("category_id"),
                 "price":price,"currency_id":"MXN","available_quantity":1,
                 "buying_mode":"buy_it_now","listing_type_id":lt,"condition":"new",
                 "pictures":pics,"attributes":attrs,"sale_terms":s.get("sale_terms",[])}
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    print(f"  publish http={r.status_code}")
    if r.status_code<300:
        j=r.json(); print(f"  NEW={j.get('id')} status={j.get('status')} price={j.get('price')}")
    else:
        print(f"  body={r.text[:400]}")
print("\nDONE")
