#!/usr/bin/env python3
import os,time,json,requests
API="https://api.mercadolibre.com"; SELLER=3629038896; T=25
IDS=["MLM6154084098","MLM6154081360","MLM3438311607","MLM3438302099","MLM6154084238","MLM3438302091","MLM6154083254","MLM6154083792","MLM3438313813","MLM3438314633","MLM6154007142","MLM6154007138","MLM6154083626","MLM3438299333","MLM3438301245","MLM6153842376","MLM3438301787","MLM3438313975","MLM3438302291","MLM6153842386","MLM6154019214","MLM6154083256","MLM6153682306","MLM3438301603","MLM3438302377","MLM3438304095","MLM3438303611","MLM3438315613"]
access=open("/tmp/ale_access_token").read().strip()
H={"Authorization":f"Bearer {access}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError(f"Token no corresponde a Alejandra: {me.json()['id']}")

validated={}
for iid in IDS:
 r=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); r.raise_for_status(); x=r.json()
 if int(x.get("seller_id") or 0)!=SELLER: raise RuntimeError(f"{iid} no pertenece a Alejandra")
 validated[iid]={"title":x.get("title"),"status":x.get("status"),"qty":x.get("available_quantity"),"inventory_id":x.get("inventory_id")}
print("ALE_AUTOSTOCK_VALIDATED="+json.dumps({"count":len(validated),"items":validated},ensure_ascii=False),flush=True)

DURATION=5*3600+30*60; start=time.time(); tick=0; changes=0
while time.time()-start<DURATION:
 tick+=1; cycle=[]
 for iid in IDS:
  try:
   r=requests.get(f"{API}/items/{iid}",headers=H,timeout=T)
   if r.status_code==401: raise RuntimeError("access token expired")
   if r.status_code!=200:
    cycle.append({"id":iid,"error":f"GET {r.status_code}"}); continue
   x=r.json(); status=x.get("status"); qty=int(x.get("available_quantity") or 0)
   if status=="active" and qty>=1: continue
   payload={"available_quantity":1}
   if status!="active": payload["status"]="active"
   u=requests.put(f"{API}/items/{iid}",headers=HJ,json=payload,timeout=T)
   row={"id":iid,"before_status":status,"before_qty":qty,"http":u.status_code}
   if u.status_code in (200,201):
    changes+=1; row["result"]="restocked_active"
   else: row["error"]=u.text[:400]
   cycle.append(row)
  except Exception as e: cycle.append({"id":iid,"error":str(e)[:300]})
 if tick==1 or cycle or tick%10==0:
  print("ALE_AUTOSTOCK_TICK="+json.dumps({"tick":tick,"elapsed":int(time.time()-start),"events":cycle,"total_changes":changes},ensure_ascii=False),flush=True)
 if tick==1:
  print("ALE_AUTOSTOCK_READY="+json.dumps({"seller":SELLER,"count":len(IDS),"interval_seconds":30,"unlimited":True},ensure_ascii=False),flush=True)
 elapsed=(time.time()-start)%30
 time.sleep(max(1,30-elapsed))
print(f"ALE_AUTOSTOCK_END ticks={tick} changes={changes}",flush=True)
