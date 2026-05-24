import os, requests, time
import meli_token
API="https://api.mercadolibre.com"
CPID="MLM70126788"; PRICE=798; SRC="MLM2952545353"
at=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {at}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print("cuenta AH:",me.get("id"),me.get("nickname"),me.get("first_name"),me.get("last_name"))
src=requests.get(f"{API}/items/{SRC}?attributes=category_id,listing_type_id,condition",headers=H,timeout=20).json()
cat=src.get("category_id"); lt=src.get("listing_type_id") or "gold_pro"
print("source cat:",cat,"listing_type:",lt)
payload={"site_id":"MLM","catalog_product_id":CPID,"catalog_listing":True,
         "price":PRICE,"currency_id":"MXN","available_quantity":1,
         "buying_mode":"buy_it_now","listing_type_id":lt,"condition":"new"}
if cat: payload["category_id"]=cat
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
