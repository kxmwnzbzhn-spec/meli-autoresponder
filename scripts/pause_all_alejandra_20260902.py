#!/usr/bin/env python3
import json, os, time, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API="https://api.mercadolibre.com"; UID=3629038896; T=30
s=requests.Session()
s.mount("https://",HTTPAdapter(max_retries=Retry(total=8,backoff_factor=1,status_forcelist=[429,500,502,503,504],allowed_methods=["GET","PUT"],respect_retry_after_header=True)))
r=s.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}; HJ={**H,"Content-Type":"application/json"}
me=s.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json().get("id",0))!=UID: raise RuntimeError(f"Cuenta incorrecta: {me.json().get('id')}")
def active_ids():
 out=[]; offset=0
 while True:
  q=s.get(f"{API}/users/{UID}/items/search",headers=H,params={"status":"active","limit":100,"offset":offset},timeout=T); q.raise_for_status()
  b=q.json(); ids=[str(x) for x in b.get("results",[])]
  out.extend(ids); offset+=len(ids)
  if not ids or offset>=int((b.get("paging") or {}).get("total",0)): break
  time.sleep(.4)
 return list(dict.fromkeys(out))
def direct_active(ids):
 out=[]
 for item_id in ids:
  q=s.get(f"{API}/items/{item_id}",headers=H,params={"attributes":"status,seller_id"},timeout=T)
  if q.status_code==200:
   j=q.json()
   if int(j.get("seller_id",0))==UID and j.get("status")=="active": out.append(item_id)
  time.sleep(.12)
 return out
before=active_ids(); candidates=list(before); paused=[]; failed=[]
for attempt in range(3):
 current=direct_active(candidates)
 if not current: break
 for item_id in current:
  rr=s.put(f"{API}/items/{item_id}",headers=HJ,json={"status":"paused"},timeout=T)
  if rr.status_code in (200,201): paused.append(item_id)
  else: failed.append({"id":item_id,"status":rr.status_code,"body":rr.text[:180]})
  time.sleep(.3)
 time.sleep(3)
 fresh=active_ids()
 candidates=list(dict.fromkeys(candidates+fresh))
remaining=direct_active(candidates)
result={"account":"Alejandra","uid":UID,"active_before":len(before),"pause_updates":len(paused),"failed":failed,"direct_active_remaining":len(remaining),"remaining_ids":remaining}
print("ALE_PAUSE_ALL="+json.dumps(result,ensure_ascii=False),flush=True)
if failed or remaining: raise RuntimeError("No quedaron todas pausadas")
