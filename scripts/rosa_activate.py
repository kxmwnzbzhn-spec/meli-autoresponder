import os,json,requests
API="https://api.mercadolibre.com"
IDS=["MLM3457517131","MLM3457517073","MLM3457506141","MLM6178069636","MLM3457506137","MLM3457506149","MLM6178069536"]
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
tok=None
for app_e,sec_e in [("MELI_APP_ID","MELI_APP_SECRET"),("MELI_APP_ID_NEW","MELI_APP_SECRET_NEW")]:
 app=os.environ.get(app_e); sec=os.environ.get(sec_e)
 if not app or not sec: continue
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":app,"client_secret":sec,"refresh_token":rt},timeout=30)
 if r.status_code==200: tok=r.json(); print(f"[auth] OK {app_e}"); break
if not tok: raise SystemExit("no auth")
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print(f"[me] uid={me.get('id')} nick={me.get('nickname')}")
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}?attributes=id,title,status,sub_status,available_quantity",headers=H,timeout=20).json()
 body={"available_quantity":1}
 if g.get("status")!="active": body["status"]="active"
 need_update = (g.get("status")!="active") or (int(g.get("available_quantity") or 0)!=1)
 if need_update:
  p=requests.put(f"{API}/items/{iid}",headers={**H,"Content-Type":"application/json"},json=body,timeout=30)
  a=requests.get(f"{API}/items/{iid}?attributes=id,status,available_quantity",headers=H,timeout=20).json()
  print(json.dumps({"iid":iid,"title":g.get("title"),"before":{"status":g.get("status"),"qty":g.get("available_quantity")},"put":p.status_code,"err":(p.text[:200] if p.status_code>=300 else ''),"after":a},ensure_ascii=False))
 else:
  print(json.dumps({"iid":iid,"title":g.get("title"),"already_ok":True,"status":g.get("status"),"qty":g.get("available_quantity")},ensure_ascii=False))
