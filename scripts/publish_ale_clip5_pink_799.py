#!/usr/bin/env python3
import json, os, requests
API="https://api.mercadolibre.com"
TARGET_SELLER=3629038896
CATALOG_PRODUCT_ID="MLM35713227"
CATEGORY_ID="MLM59800"
TITLE="Bocina Portátil Bluetooth Jbl Clip 5 Rosa 127V"
PRICE=799
TIMEOUT=40

r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],
 "client_secret":os.environ["MELI_APP_SECRET_NEW"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=TIMEOUT)
r.raise_for_status(); auth=r.json()
open("/tmp/ale_rotated_token","w").write(auth["refresh_token"])
H={"Authorization":f"Bearer {auth['access_token']}"}
HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=TIMEOUT); me.raise_for_status()
if int(me.json()["id"])!=TARGET_SELLER: raise RuntimeError(f"Cuenta incorrecta: {me.json()['id']}")

def target_ids():
 off=0
 while True:
  q=requests.get(f"{API}/users/{TARGET_SELLER}/items/search",headers=H,params={"limit":100,"offset":off},timeout=TIMEOUT)
  q.raise_for_status(); ids=q.json().get("results") or []
  yield from ids
  if len(ids)<100:return
  off+=100

existing=None
for iid in target_ids():
 q=requests.get(f"{API}/items/{iid}",headers=H,timeout=TIMEOUT)
 if q.status_code!=200: continue
 x=q.json()
 if x.get("catalog_product_id")==CATALOG_PRODUCT_ID and x.get("condition")=="new" and not x.get("deleted"):
  existing=x; break

if existing:
 u=requests.put(f"{API}/items/{existing['id']}",headers=HJ,json={"price":PRICE,"available_quantity":1,"status":"active"},timeout=TIMEOUT)
 print(f"PUT_HTTP={u.status_code} PUT_BODY={u.text[:1200]}",flush=True)
 if u.status_code not in (200,201): raise RuntimeError(f"Actualizacion fallo {u.status_code}: {u.text[:1500]}")
 target_id=existing["id"]; action="reused"
else:
 payload={
  "site_id":"MLM","family_name":TITLE[:60],"category_id":CATEGORY_ID,
  "price":PRICE,"currency_id":"MXN","available_quantity":1,"buying_mode":"buy_it_now",
  "listing_type_id":"gold_special","condition":"new",
  "catalog_product_id":CATALOG_PRODUCT_ID,"catalog_listing":True,
  "attributes":[{"id":"ITEM_CONDITION","value_name":"Nuevo"}],
  "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False}}
 p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=TIMEOUT)
 print(f"POST_HTTP={p.status_code} POST_BODY={p.text[:1800]}",flush=True)
 if p.status_code not in (200,201): raise RuntimeError(f"Publicacion fallo {p.status_code}: {p.text[:1800]}")
 target_id=p.json()["id"]; action="created"

v=requests.get(f"{API}/items/{target_id}",headers=H,timeout=TIMEOUT); v.raise_for_status(); item=v.json()
checks={"seller":int(item.get("seller_id") or 0)==TARGET_SELLER,"active":item.get("status")=="active","price":float(item.get("price") or 0)==PRICE,"quantity":int(item.get("available_quantity") or 0)==1,"new":item.get("condition")=="new","catalog":item.get("catalog_product_id")==CATALOG_PRODUCT_ID,"catalog_listing":bool(item.get("catalog_listing"))}
if not all(checks.values()): raise RuntimeError(f"Verificacion fallo: {checks}")
print("ALE_CLIP5_PINK_RESULT="+json.dumps({"action":action,"id":target_id,"title":item.get("title"),"price":item.get("price"),"quantity":item.get("available_quantity"),"condition":item.get("condition"),"status":item.get("status"),"catalog_product_id":CATALOG_PRODUCT_ID,"permalink":item.get("permalink"),"checks":checks},ensure_ascii=False),flush=True)
