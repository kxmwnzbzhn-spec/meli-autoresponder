import os, requests, time
API="https://api.mercadolibre.com"
def tok(rt):
    return requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20).json()
tc=tok(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]); TC=tc["access_token"]
print(f"NEW_RT_CLARIBEL={tc.get('refresh_token')}")
HC={"Authorization":f"Bearer {TC}"}; HJC={**HC,"Content-Type":"application/json"}
tw=tok(os.environ["MELI_REFRESH_TOKEN_WILBERT"]); TW=tw["access_token"]
print(f"NEW_RT_WILBERT={tw.get('refresh_token')}")
HW={"Authorization":f"Bearer {TW}"}

PLAN=[
  ("ELEC-009","JBL-GO4-CAMUFLAJE","MLM43902928","MLM5351937060"),
  ("ELEC-010","JBL-GO4-ROJO","MLM44710313","MLM5354755946"),
]
for alegra,sku,cpid,src_mlm in PLAN:
    src=requests.get(f"{API}/items/{src_mlm}",headers=HW,params={"attributes":"title,category_id,price"},timeout=20).json()
    cat=src.get("category_id"); title=(src.get("title") or "")[:60]; price=src.get("price") or 499
    print(f"\n=== {alegra} {cpid} src={src_mlm} cat={cat} price={price} ===")
    payload={
        "site_id":"MLM","title":title,"category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True},
        "attributes":[{"id":"SELLER_SKU","value_name":alegra}]
    }
    r=requests.post(f"{API}/items",headers=HJC,json=payload,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        print(f"  PUBLISHED: {d['id']} status={d.get('status')} price=${d.get('price')}")
    else:
        print(f"  FAIL {r.status_code} {r.text[:600]}")
    time.sleep(1.0)
