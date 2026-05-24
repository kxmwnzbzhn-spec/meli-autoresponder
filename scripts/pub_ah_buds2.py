import os, requests, time
import meli_token
API="https://api.mercadolibre.com"
CPID="MLM70126788"; PRICE=798; SRC="MLM2952545353"
at=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {at}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print("cuenta AH:",me.get("id"),me.get("nickname"))
full=requests.get(f"{API}/items/{SRC}",headers=H,timeout=20).json()
cat=full.get("category_id"); lt=full.get("listing_type_id") or "gold_pro"
prod=requests.get(f"{API}/products/{CPID}",headers=H,timeout=20).json()
if not cat: cat=prod.get("category_id")
if not cat:
    dd=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"limit":1,"q":(prod.get('name') or 'audifonos buds 2')[:60]},headers=H,timeout=15).json()
    if isinstance(dd,list) and dd: cat=dd[0].get("category_id")
print("category_id:",cat,"| listing_type:",lt,"| prod:",prod.get("name"))
payload={"site_id":"MLM","catalog_product_id":CPID,"catalog_listing":True,"category_id":cat,
         "price":PRICE,"currency_id":"MXN","available_quantity":1,
         "buying_mode":"buy_it_now","listing_type_id":lt,"condition":"new"}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print("publish http=",r.status_code)
if r.status_code<300:
    nid=r.json().get("id"); print("NEW:",nid,"status",r.json().get("status"))
    time.sleep(2)
    pw=requests.get(f"{API}/items/{nid}/price_to_win?version=v2",headers=H,timeout=10).json()
    print("PTW:",pw.get("status"),"ptw=",pw.get("price_to_win"))
else:
    print("body:",r.text[:500])
print("DONE")
