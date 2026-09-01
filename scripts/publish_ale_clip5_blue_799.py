#!/usr/bin/env python3
import json, os, requests
API="https://api.mercadolibre.com"
SOURCE_ID="MLM4780598816"
TARGET_SELLER=3629038896
PRICE=799
TIMEOUT=40

def refresh():
    r=requests.post(f"{API}/oauth/token",data={
      "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],
      "client_secret":os.environ["MELI_APP_SECRET_NEW"],
      "refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=TIMEOUT)
    r.raise_for_status(); d=r.json()
    open("/tmp/ale_rotated_token","w").write(d["refresh_token"])
    return d["access_token"]

access=refresh()
H={"Authorization":f"Bearer {access}"}
HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=TIMEOUT); me.raise_for_status()
if int(me.json()["id"])!=TARGET_SELLER: raise RuntimeError(f"Cuenta incorrecta: {me.json()['id']}")

r=requests.get(f"{API}/items/{SOURCE_ID}",timeout=TIMEOUT)
if r.status_code!=200:
    r=requests.get(f"{API}/items/{SOURCE_ID}",headers=H,timeout=TIMEOUT)
r.raise_for_status(); src=r.json()
if src.get("condition")!="new": raise RuntimeError(f"Condicion fuente inesperada: {src.get('condition')}")
catalog=src.get("catalog_product_id")
if not catalog: raise RuntimeError("La publicación fuente no expone catalog_product_id")
expected_title="Bocina Jbl Clip 5 Bluetooth Ultra Portátil Ip67 12 Horas"
print("SOURCE="+json.dumps({"id":src.get("id"),"title":src.get("title"),"catalog_product_id":catalog,"category_id":src.get("category_id"),"condition":src.get("condition")},ensure_ascii=False),flush=True)

def all_target_ids():
    off=0
    while True:
      q=requests.get(f"{API}/users/{TARGET_SELLER}/items/search",headers=H,params={"limit":100,"offset":off},timeout=TIMEOUT)
      q.raise_for_status(); ids=q.json().get("results") or []
      yield from ids
      if len(ids)<100:return
      off+=100

existing=None
for iid in all_target_ids():
    q=requests.get(f"{API}/items/{iid}",headers=H,timeout=TIMEOUT)
    if q.status_code!=200: continue
    x=q.json()
    if x.get("catalog_product_id")==catalog and x.get("condition")=="new" and not x.get("deleted"):
      existing=x; break

if existing:
    u=requests.put(f"{API}/items/{existing['id']}",headers=HJ,json={"price":PRICE,"available_quantity":1,"status":"active"},timeout=TIMEOUT)
    if u.status_code not in (200,201): raise RuntimeError(f"Actualizacion fallo {u.status_code}: {u.text[:1500]}")
    target_id=existing["id"]; action="reused"
else:
    attrs=[]
    seen=set()
    for a in src.get("attributes") or []:
      aid=a.get("id")
      if aid not in {"GTIN","EAN","UPC","ITEM_CONDITION"} or aid in seen: continue
      if aid in {"GTIN","EAN","UPC"}:
        v=str(a.get("value_name") or "").strip()
        if not(v.isdigit() and 8<=len(v)<=14): continue
        aid="GTIN"
      z={"id":aid}
      if a.get("value_id"): z["value_id"]=a["value_id"]
      if a.get("value_name"): z["value_name"]=a["value_name"]
      attrs.append(z); seen.add(aid)
    if "ITEM_CONDITION" not in seen: attrs.append({"id":"ITEM_CONDITION","value_name":"Nuevo"})
    shipping=src.get("shipping") or {}
    payload={
      "site_id":"MLM","family_name":expected_title[:60],"category_id":src["category_id"],
      "price":PRICE,"currency_id":"MXN","available_quantity":1,"buying_mode":"buy_it_now",
      "listing_type_id":src.get("listing_type_id") or "gold_special","condition":"new",
      "catalog_product_id":catalog,"catalog_listing":True,"attributes":attrs,
      "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":bool(shipping.get("free_shipping"))}}
    p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=TIMEOUT)
    print(f"POST_HTTP={p.status_code} POST_BODY={p.text[:1800]}",flush=True)
    if p.status_code not in (200,201): raise RuntimeError(f"Publicacion fallo {p.status_code}: {p.text[:1800]}")
    target_id=p.json()["id"]; action="created"

v=requests.get(f"{API}/items/{target_id}",headers=H,timeout=TIMEOUT); v.raise_for_status(); item=v.json()
checks={
 "seller":int(item.get("seller_id") or 0)==TARGET_SELLER,
 "active":item.get("status")=="active",
 "price":float(item.get("price") or 0)==PRICE,
 "quantity":int(item.get("available_quantity") or 0)==1,
 "new":item.get("condition")=="new",
 "catalog":item.get("catalog_product_id")==catalog,
 "catalog_listing":bool(item.get("catalog_listing"))}
if not all(checks.values()): raise RuntimeError(f"Verificacion fallo: {checks}")
print("ALE_CLIP5_RESULT="+json.dumps({"action":action,"id":target_id,"title":item.get("title"),"price":item.get("price"),"quantity":item.get("available_quantity"),"condition":item.get("condition"),"status":item.get("status"),"catalog_product_id":catalog,"permalink":item.get("permalink"),"checks":checks},ensure_ascii=False),flush=True)
