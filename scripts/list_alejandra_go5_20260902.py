#!/usr/bin/env python3
import json, os, re, time, requests
API="https://api.mercadolibre.com"; UID=3629038896; T=30
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json().get("id",0))!=UID: raise RuntimeError("Token no corresponde a Alejandra")
ids=[]; off=0
while True:
 q=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":100,"offset":off},timeout=T); q.raise_for_status()
 b=q.json(); batch=[str(x) for x in b.get("results",[])]; ids.extend(batch); off+=len(batch)
 if not batch or off>=int((b.get("paging") or {}).get("total",0)): break
ids=list(dict.fromkeys(ids)); rows=[]; all_rows=[]
for item_id in ids:
 endpoint=f"{API}/user-products/{item_id}" if item_id.startswith("MLMU") else f"{API}/items/{item_id}"
 q=requests.get(endpoint,headers=H,timeout=T)
 if q.status_code!=200:
  all_rows.append({"id":item_id,"http":q.status_code}); continue
 item=q.json(); title=item.get("title") or item.get("name") or item.get("family_name") or ""
 attrs=" ".join(str(a.get("value_name") or a.get("value") or "") for a in item.get("attributes") or [])
 row={"id":item_id,"title":title,"status":item.get("status"),"price":item.get("price"),"catalog_product_id":item.get("catalog_product_id"),"permalink":item.get("permalink")}
 all_rows.append(row)
 if re.search(r"(?i)(?:\\bgo\\s*5\\b|\\bgo5\\b)",title+" "+attrs): rows.append(row)
 time.sleep(.2)
rows.sort(key=lambda x:(x["title"],x["id"]))
print("ALE_GO5="+json.dumps({"scanned":len(ids),"count":len(rows),"items":rows,"all":all_rows},ensure_ascii=False),flush=True)
