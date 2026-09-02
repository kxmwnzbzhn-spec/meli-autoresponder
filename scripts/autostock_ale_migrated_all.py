#!/usr/bin/env python3
import json, os, time, requests
API="https://api.mercadolibre.com"; SELLER=3629038896; T=25
IDS=json.load(open("config/ale_autostock_migrated_ids.json"))
if not IDS: raise RuntimeError("Lista migrada vacía")
access=open("/tmp/ale_access_token").read().strip()
H={"Authorization":f"Bearer {access}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError("Token no corresponde a Alejandra")
print("ALE_MIGRATED_AUTOSTOCK_READY="+json.dumps({"count":len(IDS),"ids":IDS}),flush=True)
start=time.time(); tick=0
while time.time()-start<5*3600+30*60:
 tick+=1; events=[]
 for iid in IDS:
  try:
   r=requests.get(f"{API}/items/{iid}",headers=H,timeout=T)
   if r.status_code!=200: events.append({"id":iid,"get":r.status_code}); continue
   x=r.json(); qty=int(x.get("available_quantity") or 0); status=x.get("status")
   if status=="active" and qty==1: continue
   u=requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1,"status":"active"},timeout=T)
   events.append({"id":iid,"before_status":status,"before_qty":qty,"http":u.status_code})
  except Exception as e: events.append({"id":iid,"error":str(e)[:200]})
 if tick==1 or events or tick%10==0: print("ALE_MIGRATED_TICK="+json.dumps({"tick":tick,"events":events},ensure_ascii=False),flush=True)
 time.sleep(30)
