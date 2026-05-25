import os, requests, json
import meli_token
CP="MLM65349937"; CAT="MLM194115"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
p=requests.get(f"{API}/products/{CP}",headers=H,timeout=20).json()
title=p.get("name")
# EMPTY_GTIN_REASON valido
egr=None
ca=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=20).json()
for a in ca:
    if a.get("id")=="EMPTY_GTIN_REASON":
        for v in (a.get("values") or []):
            if "no tiene" in (v.get("name") or "").lower(): egr=v.get("id")
        if not egr and a.get("values"): egr=a["values"][-1]["id"]
# fotos
allah=[]; sess=requests.Session()
for pic in (p.get("pictures") or []):
    url=pic.get("secure_url") or pic.get("url")
    if not url: continue
    img=sess.get(url,timeout=60).content
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,files={"file":("p.jpg",img,"image/jpeg")},timeout=120)
    if rp.status_code<300: allah.append(rp.json().get("id"))
print("egr:",egr,"| fotos:",len(allah))
sizes=["S","M","L","XL"]
vars=[]
for sz in sizes:
    va=[{"id":"EMPTY_GTIN_REASON","value_id":egr}] if egr else []
    vars.append({"attribute_combinations":[{"id":"SIZE","value_name":sz}],
                 "attributes":va,"picture_ids":allah[:10],"available_quantity":3,"price":299})
attrs=[{"id":"BRAND","value_name":"Calvin Klein"},{"id":"MODEL","value_name":"Brief"},
       {"id":"GENDER","value_name":"Sin género"},{"id":"COLOR","value_name":"Mixto"}]
if egr: attrs.append({"id":"EMPTY_GTIN_REASON","value_id":egr})
payload={"site_id":"MLM","title":title,"category_id":CAT,"currency_id":"MXN",
         "buying_mode":"buy_it_now","listing_type_id":"gold_special","condition":"new",
         "pictures":[{"id":x} for x in allah],"attributes":attrs,"variations":vars}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=60)
print("publish http:",r.status_code)
if r.status_code<300:
    print("NEW:",r.json().get("id"),"PERMALINK:",r.json().get("permalink"))
else:
    print("body:",r.text[:700])
print("DONE")
