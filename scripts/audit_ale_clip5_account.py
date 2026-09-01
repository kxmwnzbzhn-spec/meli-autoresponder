#!/usr/bin/env python3
import os,json,requests
API="https://api.mercadolibre.com"; T=30
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); a=r.json(); open("/tmp/ale_rotated_token","w").write(a["refresh_token"])
H={"Authorization":f"Bearer {a['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status(); user=me.json()
wanted=["MLM3438315613","MLM3438303611","MLM6154085738","MLM3438304095","MLM6154086230"]
off=0; allids=[]
while True:
 q=requests.get(f"{API}/users/{user['id']}/items/search",headers=H,params={"limit":100,"offset":off,"search_type":"scan"},timeout=T)
 if q.status_code!=200:
  q=requests.get(f"{API}/users/{user['id']}/items/search",headers=H,params={"limit":100,"offset":off},timeout=T)
 q.raise_for_status(); ids=q.json().get("results") or []; allids+=ids
 if len(ids)<100: break
 off+=100
rows=[]
for iid in wanted:
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=T)
 rows.append({"id":iid,"http":g.status_code,**({k:g.json().get(k) for k in ["seller_id","title","status","sub_status","available_quantity","price","catalog_product_id","permalink","date_created","last_updated"]} if g.status_code==200 else {"body":g.text[:500]}),"present_in_account_search":iid in allids})
print("ALE_ACCOUNT_AUDIT="+json.dumps({"me":{k:user.get(k) for k in ["id","nickname","first_name","last_name","email","status","site_id"]},"total_items":len(allids),"items":rows},ensure_ascii=False),flush=True)
