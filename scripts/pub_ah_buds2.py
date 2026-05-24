import os, requests, time
import meli_token
API="https://api.mercadolibre.com"
CPID="MLM70126788"; PRICE=798; SRC="MLM2952545353"
at=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {at}"}; HJ={**H,"Content-Type":"application/json"}
full=requests.get(f"{API}/items/{SRC}",headers=H,timeout=20).json()
cat=full.get("category_id") or "MLM6777"; lt=full.get("listing_type_id") or "gold_pro"; title=full.get("title")
print("title:",title,"| cat:",cat)
def attempt(payload,label):
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"[{label}] http={r.status_code}")
    if r.status_code<300:
        nid=r.json().get("id"); print("  NEW:",nid,"status",r.json().get("status"))
        return True
    print("  body:",r.text[:280]); return False
base={"site_id":"MLM","catalog_product_id":CPID,"catalog_listing":True,"category_id":cat,
      "price":PRICE,"currency_id":"MXN","available_quantity":1,"buying_mode":"buy_it_now",
      "listing_type_id":lt,"condition":"new"}
# intento 1: con title
p1=dict(base); p1["title"]=title
if not attempt(p1,"con_title"):
    # intento 2: title + sin catalog_listing flag explicito? probamos catalog_listing True ya está; probamos sin category
    p2=dict(base); p2["title"]=title; p2.pop("category_id",None)
    attempt(p2,"con_title_sin_cat")
print("DONE")
