#!/usr/bin/env python3
import json, os, requests
API="https://api.mercadolibre.com"; SELLER=3629038896; T=30
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],
 "client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]
},timeout=T); r.raise_for_status(); tok=r.json()
open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError("Token no corresponde a Alejandra")
ids=[]; offset=0
while True:
 q=requests.get(f"{API}/users/{SELLER}/items/search",headers=H,params={"limit":100,"offset":offset},timeout=T)
 q.raise_for_status(); batch=q.json().get("results") or []; ids.extend(batch)
 if len(batch)<100: break
 offset+=100
items=[]
for iid in ids:
 x=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); x.raise_for_status(); d=x.json()
 if d.get("deleted"): continue
 items.append({"id":d["id"],"title":d.get("title"),"status":d.get("status"),"qty":d.get("available_quantity"),"price":d.get("price"),"condition":d.get("condition"),"catalog_product_id":d.get("catalog_product_id"),"catalog_listing":d.get("catalog_listing"),"date_created":d.get("date_created")})
print("ALE_INVENTORY="+json.dumps({"count":len(items),"items":items},ensure_ascii=False),flush=True)
