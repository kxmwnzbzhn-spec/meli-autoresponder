#!/usr/bin/env python3
import os, json, requests
API="https://api.mercadolibre.com"
IDS=["MLM3457506231","MLM3457506229","MLM3457506223","MLM3457517095","MLM3457517089"]
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
tok=None
for app_e,sec_e in [("MELI_APP_ID","MELI_APP_SECRET"),("MELI_APP_ID_NEW","MELI_APP_SECRET_NEW")]:
 app=os.environ.get(app_e); sec=os.environ.get(sec_e)
 if not app or not sec: continue
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":app,"client_secret":sec,"refresh_token":rt},timeout=30)
 if r.status_code==200:
  tok=r.json(); print(f"[auth] OK con {app_e}"); break
 else:
  print(f"[auth] {app_e} → {r.status_code} {r.text[:200]}")
if not tok: raise SystemExit("no auth")
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print(f"[me] uid={me.get('id')} nick={me.get('nickname')}")
SELLER=int(me.get("id"))
out=[]
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}?attributes=id,title,status,price,seller_id",headers=H,timeout=20)
 before=g.json() if g.status_code==200 else {"http":g.status_code,"err":g.text[:200]}
 if before.get("seller_id") and int(before["seller_id"])!=SELLER:
  out.append({"item":iid,"error":f"seller mismatch {before.get('seller_id')} vs {SELLER}"}); print(json.dumps(out[-1])); continue
 p=requests.put(f"{API}/items/{iid}",headers={**H,"Content-Type":"application/json"},json={"status":"paused"},timeout=30)
 a=requests.get(f"{API}/items/{iid}?attributes=id,status",headers=H,timeout=20).json()
 row={"item":iid,"title":before.get("title"),"before":before.get("status"),"put":p.status_code,"after":a.get("status")}
 if p.status_code not in (200,201): row["err"]=p.text[:300]
 out.append(row); print(json.dumps(row,ensure_ascii=False))
with open("rosa_pause_result.json","w") as f: json.dump({"seller":SELLER,"nickname":me.get("nickname"),"items":out},f,indent=2,ensure_ascii=False)
