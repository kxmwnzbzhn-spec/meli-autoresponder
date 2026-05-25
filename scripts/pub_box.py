import os, requests, json
import meli_token
CP="MLM65349937"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
p=requests.get(f"{API}/products/{CP}",headers=H,timeout=20).json()
title=p.get("name")
# categoria via domain_discovery
it=requests.get(f"{API}/products/{CP}/items",headers=H,timeout=15).json().get("results") or []
cat=None
if it:
    ci=requests.get(f"{API}/items/{it[0].get('item_id')}?attributes=category_id",headers=H,timeout=12).json()
    cat=ci.get("category_id")
prices=[o.get("price") for o in it if o.get("price")]
price=min(prices) if prices else 299
# EMPTY_GTIN_REASON valido para la categoria
egr=None; size_attr="CLOTHING_LOT_SIZE"
if cat:
    ca=requests.get(f"{API}/categories/{cat}/attributes",headers=H,timeout=20).json()
    for a in ca:
        if a.get("id")=="EMPTY_GTIN_REASON":
            for v in (a.get("values") or []):
                if "no tiene" in (v.get("name") or "").lower(): egr=v.get("id")
            if not egr and a.get("values"): egr=a["values"][-1]["id"]
print("cat:",cat,"| price:",price,"| egr:",egr)
# subir fotos
allah=[]
sess=requests.Session()
for pic in (p.get("pictures") or []):
    url=pic.get("secure_url") or pic.get("url")
    if not url: continue
    img=sess.get(url,timeout=60).content
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,files={"file":("p.jpg",img,"image/jpeg")},timeout=120)
    if rp.status_code<300: allah.append(rp.json().get("id"))
print("fotos:",len(allah))
def build(brand, with_egr):
    item_attrs=[{"id":"BRAND","value_name":brand},{"id":"MODEL","value_name":"Brief"},
                {"id":"COLOR","value_name":"Mixto"},{"id":"ITEMS_NUMBER","value_name":"3"},
                {"id":"GENDER","value_name":"Sin género"}]
    if with_egr and egr: item_attrs.append({"id":"EMPTY_GTIN_REASON","value_id":egr})
    vars=[]
    for sz in ["S","M","L","XL"]:
        v={"attribute_combinations":[{"id":size_attr,"value_name":sz}],
           "picture_ids":allah[:10] or [],"available_quantity":3,"price":price}
        if with_egr and egr: v["attributes"]=[{"id":"EMPTY_GTIN_REASON","value_id":egr}]
        vars.append(v)
    return {"site_id":"MLM","title":title,"category_id":cat,"currency_id":"MXN",
            "buying_mode":"buy_it_now","listing_type_id":"gold_special","condition":"new",
            "pictures":[{"id":x} for x in allah],"attributes":item_attrs,"variations":vars}
for brand,egrf in [("Calvin Klein",True),("Genérico",True),("Genérico",False)]:
    r=requests.post(f"{API}/items",headers=HJ,json=build(brand,egrf),timeout=60)
    print(f"try brand={brand} egr={egrf} -> http={r.status_code}")
    if r.status_code<300:
        nid=r.json().get("id"); print("NEW:",nid,"status:",r.json().get("status"),"PERMALINK:",r.json().get("permalink"))
        break
    else:
        print("  body:",r.text[:300])
print("DONE")
