#!/usr/bin/env python3
import json, os, re, time, requests
API="https://api.mercadolibre.com"; UID=3629038896; T=30
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json().get("id",0))!=UID: raise RuntimeError("Token no corresponde a Alejandra")
ids=[]
for status in ("active","paused"):
 off=0
 while True:
  q=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"status":status,"limit":100,"offset":off},timeout=T); q.raise_for_status()
  b=q.json(); batch=[str(x) for x in b.get("results",[])]; ids.extend(batch); off+=len(batch)
  if not batch or off>=int((b.get("paging") or {}).get("total",0)): break
ids=list(dict.fromkeys(ids)); rows=[]
for p in range(0,len(ids),20):
 batch=ids[p:p+20]
 q=requests.get(f"{API}/items",headers=H,params={"ids":",".join(batch)},timeout=T); q.raise_for_status()
 for wrap in q.json():
  item=wrap.get("body") or {}; title=item.get("title") or ""
  if re.search(r"(?i)(?:\bgo\s*5\b|\bgo5\b)",title):
   rows.append({"id":item.get("id"),"title":title,"status":item.get("status"),"price":item.get("price"),"catalog_listing":item.get("catalog_listing"),"permalink":item.get("permalink")})
 time.sleep(.3)
rows.sort(key=lambda x:(x["title"],x["id"]))
print("ALE_GO5="+json.dumps({"count":len(rows),"items":rows},ensure_ascii=False),flush=True)
