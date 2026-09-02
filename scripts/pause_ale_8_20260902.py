#!/usr/bin/env python3
import os,json,requests
API="https://api.mercadolibre.com"; SELLER=3629038896; T=30
IDS=["MLM6154085738","MLM6153682306","MLM3438304095","MLM6154086230","MLM3438303611","MLM3438315613","MLM6153842386","MLM6154019214"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); a=r.json(); open("/tmp/ale_rotated_token","w").write(a["refresh_token"])
H={"Authorization":f"Bearer {a['access_token']}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError("Token no corresponde a Alejandra")
rows=[]
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); g.raise_for_status(); before=g.json()
 if int(before.get("seller_id") or 0)!=SELLER: raise RuntimeError(f"{iid} no pertenece a Alejandra")
 u=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=T)
 if u.status_code not in (200,201): raise RuntimeError(f"{iid} pause failed {u.status_code}: {u.text[:800]}")
 v=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); v.raise_for_status(); after=v.json()
 if after.get("status")!="paused": raise RuntimeError(f"{iid} no quedó pausada: {after.get('status')}")
 rows.append({"id":iid,"title":after.get("title"),"before":before.get("status"),"after":after.get("status"),"qty":after.get("available_quantity"),"sub_status":after.get("sub_status")})
print("ALE_PAUSE_RESULT="+json.dumps(rows,ensure_ascii=False),flush=True)
