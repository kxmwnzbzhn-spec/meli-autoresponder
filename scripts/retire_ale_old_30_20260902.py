#!/usr/bin/env python3
import json, os, requests
API="https://api.mercadolibre.com"; SELLER=3629038896; T=30
OLD_IDS=["MLM6154086230","MLM6154085738","MLM6154084238","MLM6154084098","MLM6154083792","MLM6154083626","MLM6154083256","MLM6154083254","MLM6154081360","MLM6154019214","MLM6154007142","MLM6154007138","MLM6153842386","MLM6153842376","MLM6153682306","MLM3438315613","MLM3438314633","MLM3438313975","MLM3438313813","MLM3438311607","MLM3438304095","MLM3438303611","MLM3438302377","MLM3438302291","MLM3438302099","MLM3438302091","MLM3438301787","MLM3438301603","MLM3438301245","MLM3438299333"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError("Token no corresponde a Alejandra")
results=[]
for iid in OLD_IDS:
 before=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); before.raise_for_status(); b=before.json()
 if int(b.get("seller_id") or 0)!=SELLER: raise RuntimeError(f"{iid} no pertenece a Alejandra")
 close_http=None
 if b.get("status")!="closed" and not b.get("deleted"):
  c=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=T); close_http=c.status_code
 d=requests.delete(f"{API}/items/{iid}",headers=H,timeout=T)
 after=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); after.raise_for_status(); a=after.json()
 row={"id":iid,"before":b.get("status"),"close_http":close_http,"delete_http":d.status_code,"after":a.get("status"),"deleted":a.get("deleted"),"sub_status":a.get("sub_status")}
 results.append(row)
 if a.get("status")=="active": raise RuntimeError(f"{iid} sigue activo: {row}")
 print("RETIRED="+json.dumps(row,ensure_ascii=False),flush=True)
print("ALE_OLD_RETIRE_RESULT="+json.dumps({"count":len(results),"active_remaining":sum(1 for x in results if x["after"]=="active"),"deleted_true":sum(1 for x in results if x["deleted"]),"items":results},ensure_ascii=False),flush=True)
