#!/usr/bin/env python3
import json, os, requests

API="https://api.mercadolibre.com"
SOURCE_ID="MLM3438301245"
SELLER=3629038896
TIMEOUT=30

r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token",
 "client_id":os.environ["MELI_APP_ID_NEW"],
 "client_secret":os.environ["MELI_APP_SECRET_NEW"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"],
},timeout=TIMEOUT)
r.raise_for_status(); tok=r.json()
open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}
HJ={**H,"Content-Type":"application/json"}

r=requests.get(f"{API}/items/{SOURCE_ID}",headers=H,timeout=TIMEOUT)
r.raise_for_status(); s=r.json()
if int(s.get("seller_id") or 0)!=SELLER:
 raise RuntimeError(f"{SOURCE_ID} no pertenece a Alejandra")
if not s.get("catalog_product_id") or not s.get("catalog_listing"):
 raise RuntimeError(f"{SOURCE_ID} no es publicación de catálogo")

attrs=[]
seen=set()
for a in s.get("attributes") or []:
 aid=a.get("id")
 if aid not in {"GTIN","EAN","UPC","ITEM_CONDITION","GRADING"} or aid in seen:
  continue
 value=str(a.get("value_name") or "").strip()
 if aid in {"GTIN","EAN","UPC"}:
  if not (value.isdigit() and 8<=len(value)<=14):
   continue
  aid="GTIN"
 x={"id":aid}
 if a.get("value_id"): x["value_id"]=a["value_id"]
 if a.get("value_name"): x["value_name"]=a["value_name"]
 attrs.append(x); seen.add(aid)
if "ITEM_CONDITION" not in seen:
 attrs.append({"id":"ITEM_CONDITION","value_name":{"new":"Nuevo","used":"Usado","refurbished":"Reacondicionado"}[s["condition"]]})

shipping=s.get("shipping") or {}
payload={
 "site_id":"MLM",
 "family_name":(s.get("family_name") or s.get("title") or "Producto")[:60],
 "category_id":s["category_id"],
 "price":s["price"],
 "currency_id":s.get("currency_id") or "MXN",
 "available_quantity":1,
 "buying_mode":s.get("buying_mode") or "buy_it_now",
 "listing_type_id":s.get("listing_type_id") or "gold_special",
 "condition":s["condition"],
 "catalog_product_id":s["catalog_product_id"],
 "catalog_listing":True,
 "attributes":attrs,
 "shipping":{"mode":"me2","local_pick_up":bool(shipping.get("local_pick_up")),"free_shipping":bool(shipping.get("free_shipping"))},
}
terms=[]
for term in s.get("sale_terms") or []:
 if term.get("id") in {"WARRANTY_TYPE","WARRANTY_TIME"}:
  x={"id":term["id"]}
  if term.get("value_id"): x["value_id"]=term["value_id"]
  if term.get("value_name"): x["value_name"]=term["value_name"]
  terms.append(x)
if terms: payload["sale_terms"]=terms

r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=45)
print(f"CLONE_HTTP={r.status_code} BODY={r.text[:1600]}",flush=True)
if r.status_code not in (200,201):
 raise RuntimeError(f"No se pudo crear el duplicado: {r.status_code} {r.text[:1600]}")
new_id=r.json()["id"]
r=requests.get(f"{API}/items/{new_id}",headers=H,timeout=TIMEOUT)
r.raise_for_status(); n=r.json()
checks={
 "different_id":new_id!=SOURCE_ID,
 "seller":int(n.get("seller_id") or 0)==SELLER,
 "active":n.get("status")=="active",
 "quantity_one":int(n.get("available_quantity") or 0)==1,
 "same_price":float(n.get("price") or 0)==float(s.get("price") or 0),
 "same_condition":n.get("condition")==s.get("condition"),
 "same_catalog":n.get("catalog_product_id")==s.get("catalog_product_id"),
}
if not all(checks.values()): raise RuntimeError(f"Verificación falló: {checks}")
print("ALE_DUPLICATE_RESULT="+json.dumps({
 "source_id":SOURCE_ID,"new_id":new_id,"title":n.get("title"),"price":n.get("price"),
 "condition":n.get("condition"),"status":n.get("status"),"quantity":n.get("available_quantity"),
 "permalink":n.get("permalink"),"checks":checks
},ensure_ascii=False),flush=True)
